import '../../pair-components/button';
import '../../pair-components/icon_button';
import '../../pair-components/tooltip';
import '../progress/progress_stage_completed';
import './stage_description';
import './stage_footer';

import {MobxLitElement} from '@adobe/lit-mobx';
import {CSSResultGroup, html, nothing} from 'lit';
import {customElement, property, state} from 'lit/decorators.js';
import {classMap} from 'lit/directives/class-map.js';

import {core} from '../../core/core';
import {ParticipantService} from '../../services/participant.service';
import {ParticipantAnswerService} from '../../services/participant.answer';
import {FirebaseService} from '../../services/firebase.service';
import {
  AssistantShoppingStageConfig,
  AssistantShoppingStageParticipantAnswer,
  Product,
  ShoppingChatMessage,
  ShoppingListItem,
  BasketItem,
  calculateBasketTotal,
  formatPrice,
  isProductInBasket,
  createAssistantShoppingParticipantAnswer,
  StageKind,
} from '@deliberation-lab/utils';
import {
  sendAssistantShoppingMessageCallable,
  updateAssistantShoppingBasketCallable,
} from '../../shared/callables';

import {styles} from './assistant_shopping_participant_view.scss';

/** Assistant Shopping stage participant view. */
@customElement('assistant-shopping-participant-view')
export class AssistantShoppingParticipantView extends MobxLitElement {
  static override styles: CSSResultGroup = [styles];

  private readonly participantService = core.getService(ParticipantService);
  private readonly participantAnswerService = core.getService(
    ParticipantAnswerService,
  );
  private readonly firebaseService = core.getService(FirebaseService);

  @property() stage: AssistantShoppingStageConfig | null = null;

  @state() messageInput = '';
  @state() isSendingMessage = false;
  @state() isUpdatingBasket = false;
  @state() timeRemaining: number | null = null;

  private timerInterval: number | null = null;

  override connectedCallback() {
    super.connectedCallback();
    this.startTimer();
  }

  override disconnectedCallback() {
    super.disconnectedCallback();
    this.stopTimer();
  }

  private startTimer() {
    if (!this.stage?.timeLimitInMinutes) return;

    this.timerInterval = window.setInterval(() => {
      this.updateTimeRemaining();
    }, 1000);

    this.updateTimeRemaining();
  }

  private stopTimer() {
    if (this.timerInterval !== null) {
      window.clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  }

  private updateTimeRemaining() {
    if (!this.stage?.timeLimitInMinutes) {
      this.timeRemaining = null;
      return;
    }

    const answer = this.getParticipantAnswer();
    if (!answer?.startedAt) {
      // Timer hasn't started yet
      this.timeRemaining = this.stage.timeLimitInMinutes * 60;
      return;
    }

    const startTime = answer.startedAt.seconds * 1000;
    const timeLimit = this.stage.timeLimitInMinutes * 60 * 1000;
    const elapsed = Date.now() - startTime;
    const remaining = Math.max(0, Math.floor((timeLimit - elapsed) / 1000));

    this.timeRemaining = remaining;
  }

  private getParticipantAnswer(): AssistantShoppingStageParticipantAnswer | null {
    if (!this.stage) return null;
    const answer = this.participantService.answerMap[this.stage.id];
    if (answer && answer.kind === StageKind.ASSISTANT_SHOPPING) {
      return answer as AssistantShoppingStageParticipantAnswer;
    }
    return null;
  }

  private get isTimeUp(): boolean {
    return this.timeRemaining !== null && this.timeRemaining <= 0;
  }

  override render() {
    if (!this.stage) return nothing;

    const answer =
      this.getParticipantAnswer() ??
      createAssistantShoppingParticipantAnswer(this.stage.id);

    return html`
      <stage-description .stage=${this.stage}></stage-description>
      <div class="shopping-layout">
        <div class="left-panel">
          ${this.renderShoppingList(answer)}
        </div>
        <div class="center-panel">
          ${this.renderChatInterface(answer)}
        </div>
        <div class="right-panel">
          ${this.renderBasket(answer)}
        </div>
      </div>
      <stage-footer .disabled=${!this.isTimeUp}>
        ${this.stage.progress.showParticipantProgress
          ? html`<progress-stage-completed></progress-stage-completed>`
          : nothing}
        ${this.renderTimerMessage()}
      </stage-footer>
    `;
  }

  // ************************************************************************ //
  // SHOPPING LIST                                                            //
  // ************************************************************************ //

  private renderShoppingList(answer: AssistantShoppingStageParticipantAnswer) {
    if (!this.stage) return nothing;

    const basket = answer.basket;

    return html`
      <div class="panel">
        <div class="panel-header">Shopping List</div>
        <div class="shopping-list">
          ${this.stage.shoppingList.map((item) =>
            this.renderShoppingListItem(item, basket),
          )}
        </div>
      </div>
    `;
  }

  private renderShoppingListItem(item: ShoppingListItem, basket: BasketItem[]) {
    if (!this.stage) return nothing;

    // Check if any product matching this list item is in the basket
    // (Simple heuristic: check if product name contains list item name)
    const matchingProduct = basket.find((basketItem) => {
      const product = this.stage?.productCatalog.find(
        (p) => p.id === basketItem.productId,
      );
      return (
        product &&
        product.name.toLowerCase().includes(item.name.toLowerCase())
      );
    });

    const isComplete = !!matchingProduct;

    return html`
      <div class="shopping-list-item ${isComplete ? 'complete' : ''}">
        <span class="checkbox">${isComplete ? '✓' : '○'}</span>
        <div class="item-content">
          <div class="item-name">${item.name}</div>
          ${item.description
            ? html`<div class="item-description">${item.description}</div>`
            : nothing}
        </div>
      </div>
    `;
  }

  // ************************************************************************ //
  // CHAT INTERFACE                                                           //
  // ************************************************************************ //

  private renderChatInterface(answer: AssistantShoppingStageParticipantAnswer) {
    const chatHistory = answer.chatHistory;

    return html`
      <div class="panel chat-panel">
        <div class="panel-header">Chat with Shopping Assistant</div>
        <div class="chat-messages">
          ${chatHistory.length === 0
            ? html`<div class="chat-placeholder">
                Send a message to start chatting with the shopping assistant.
              </div>`
            : chatHistory.map((msg) => this.renderChatMessage(msg))}
          ${this.isSendingMessage
            ? html`<div class="chat-loading">Assistant is typing...</div>`
            : nothing}
        </div>
        <div class="chat-input-wrapper">
          <textarea
            class="chat-input"
            placeholder="Type your message..."
            .value=${this.messageInput}
            ?disabled=${this.isTimeUp || this.isSendingMessage}
            @input=${this.handleMessageInput}
            @keydown=${this.handleKeyDown}
          ></textarea>
          <pr-button
            variant="tonal"
            ?disabled=${!this.messageInput.trim() ||
            this.isTimeUp ||
            this.isSendingMessage}
            ?loading=${this.isSendingMessage}
            @click=${this.sendMessage}
          >
            Send
          </pr-button>
        </div>
      </div>
    `;
  }

  private renderChatMessage(message: ShoppingChatMessage) {
    const isUser = message.role === 'user';

    return html`
      <div class="chat-message ${isUser ? 'user' : 'assistant'}">
        <div class="message-role">${isUser ? 'You' : 'Assistant'}</div>
        <div class="message-content">${message.content}</div>
        ${message.productRecommendations?.length
          ? this.renderProductRecommendations(message.productRecommendations)
          : nothing}
      </div>
    `;
  }

  private renderProductRecommendations(
    recommendations: {productId: string; reason: string}[],
  ) {
    if (!this.stage) return nothing;

    const answer = this.getParticipantAnswer();
    const basket = answer?.basket ?? [];

    return html`
      <div class="product-recommendations">
        ${recommendations.map((rec) => {
          const product = this.stage?.productCatalog.find(
            (p) => p.id === rec.productId,
          );
          if (!product) return nothing;

          const inBasket = isProductInBasket(product.id, basket);

          return html`
            <div class="product-card">
              <div class="product-info">
                <div class="product-name">${product.name}</div>
                <div class="product-price">${formatPrice(product.price)}</div>
              </div>
              <pr-button
                size="small"
                variant=${inBasket ? 'outlined' : 'tonal'}
                color=${inBasket ? 'error' : 'primary'}
                ?disabled=${this.isTimeUp || this.isUpdatingBasket}
                @click=${() =>
                  inBasket
                    ? this.removeFromBasket(product.id)
                    : this.addToBasket(product.id)}
              >
                ${inBasket ? 'Remove' : 'Add to basket'}
              </pr-button>
            </div>
          `;
        })}
      </div>
    `;
  }

  private handleMessageInput(e: InputEvent) {
    this.messageInput = (e.target as HTMLTextAreaElement).value;
  }

  private handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      this.sendMessage();
    }
  }

  private async sendMessage() {
    if (
      !this.stage ||
      !this.messageInput.trim() ||
      this.isSendingMessage ||
      this.isTimeUp
    ) {
      return;
    }

    const message = this.messageInput.trim();
    this.messageInput = '';
    this.isSendingMessage = true;

    try {
      await sendAssistantShoppingMessageCallable(
        this.firebaseService.functions,
        {
          experimentId: this.participantService.experimentId!,
          participantPrivateId: this.participantService.profile!.privateId,
          stageId: this.stage.id,
          message,
        },
      );
    } catch (error) {
      console.error('Failed to send message:', error);
      // Restore the message input on error
      this.messageInput = message;
    } finally {
      this.isSendingMessage = false;
    }
  }

  // ************************************************************************ //
  // BASKET                                                                   //
  // ************************************************************************ //

  private renderBasket(answer: AssistantShoppingStageParticipantAnswer) {
    if (!this.stage) return nothing;

    const basket = answer.basket;
    const total = calculateBasketTotal(basket, this.stage.productCatalog);

    return html`
      <div class="panel">
        <div class="panel-header">Your Basket</div>
        <div class="basket-items">
          ${basket.length === 0
            ? html`<div class="basket-empty">Your basket is empty</div>`
            : basket.map((item) => this.renderBasketItem(item))}
        </div>
        <div class="basket-total">
          <span>Total:</span>
          <span class="total-amount">${formatPrice(total)}</span>
        </div>
      </div>
    `;
  }

  private renderBasketItem(item: BasketItem) {
    if (!this.stage) return nothing;

    const product = this.stage.productCatalog.find(
      (p) => p.id === item.productId,
    );
    if (!product) return nothing;

    return html`
      <div class="basket-item">
        <div class="basket-item-info">
          <div class="basket-item-name">${product.name}</div>
          <div class="basket-item-price">${formatPrice(product.price)}</div>
        </div>
        <pr-icon-button
          icon="delete"
          color="error"
          size="small"
          ?disabled=${this.isTimeUp || this.isUpdatingBasket}
          @click=${() => this.removeFromBasket(product.id)}
        >
        </pr-icon-button>
      </div>
    `;
  }

  private async addToBasket(productId: string) {
    if (!this.stage || this.isUpdatingBasket || this.isTimeUp) return;

    this.isUpdatingBasket = true;
    try {
      await updateAssistantShoppingBasketCallable(
        this.firebaseService.functions,
        {
          experimentId: this.participantService.experimentId!,
          participantPrivateId: this.participantService.profile!.privateId,
          stageId: this.stage.id,
          action: 'add',
          productId,
        },
      );
    } catch (error) {
      console.error('Failed to add to basket:', error);
    } finally {
      this.isUpdatingBasket = false;
    }
  }

  private async removeFromBasket(productId: string) {
    if (!this.stage || this.isUpdatingBasket || this.isTimeUp) return;

    this.isUpdatingBasket = true;
    try {
      await updateAssistantShoppingBasketCallable(
        this.firebaseService.functions,
        {
          experimentId: this.participantService.experimentId!,
          participantPrivateId: this.participantService.profile!.privateId,
          stageId: this.stage.id,
          action: 'remove',
          productId,
        },
      );
    } catch (error) {
      console.error('Failed to remove from basket:', error);
    } finally {
      this.isUpdatingBasket = false;
    }
  }

  // ************************************************************************ //
  // TIMER                                                                    //
  // ************************************************************************ //

  private renderTimerMessage() {
    if (!this.stage?.timeLimitInMinutes) return nothing;

    if (this.isTimeUp) {
      return html`
        <div class="timer-message complete">
          Time is up! You can now proceed to the next stage.
        </div>
      `;
    }

    if (this.timeRemaining !== null) {
      const minutes = Math.floor(this.timeRemaining / 60);
      const seconds = this.timeRemaining % 60;
      const timeStr = `${minutes}:${seconds.toString().padStart(2, '0')}`;

      return html`
        <div class="timer-message">
          Time remaining: ${timeStr}
        </div>
      `;
    }

    return nothing;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'assistant-shopping-participant-view': AssistantShoppingParticipantView;
  }
}
