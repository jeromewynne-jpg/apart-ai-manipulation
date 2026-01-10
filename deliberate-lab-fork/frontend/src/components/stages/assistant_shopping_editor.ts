import {MobxLitElement} from '@adobe/lit-mobx';
import {CSSResultGroup, html, nothing} from 'lit';
import {customElement, property, state} from 'lit/decorators.js';

import '@material/web/checkbox/checkbox.js';
import '@material/web/textfield/filled-text-field.js';
import '../../pair-components/textarea_template';

import {core} from '../../core/core';
import {ExperimentEditor} from '../../services/experiment.editor';

import {
  ApiKeyType,
  AssistantShoppingStageConfig,
  Product,
  ShoppingListItem,
  createProduct,
  createShoppingListItem,
} from '@deliberation-lab/utils';

import {styles} from './assistant_shopping_editor.scss';

/** Editor for Assistant Shopping stage configuration. */
@customElement('assistant-shopping-editor')
export class AssistantShoppingEditor extends MobxLitElement {
  static override styles: CSSResultGroup = [styles];

  private readonly experimentEditor = core.getService(ExperimentEditor);

  @property() stage: AssistantShoppingStageConfig | undefined = undefined;

  @state() productCatalogJson = '';
  @state() jsonError: string | null = null;

  override render() {
    if (this.stage === undefined) {
      return nothing;
    }

    return html`
      <div class="section">
        <div class="title">Shopping list</div>
        <div class="description">
          Items the participant must purchase. These are displayed as a checklist.
        </div>
        ${this.stage.shoppingList.map((item, index) =>
          this.renderShoppingListItem(item, index),
        )}
        <pr-button
          color="secondary"
          variant="tonal"
          ?disabled=${!this.experimentEditor.canEditStages}
          @click=${this.addShoppingListItem}
        >
          Add shopping list item
        </pr-button>
      </div>

      <div class="divider"></div>

      <div class="section">
        <div class="title">Product catalog</div>
        <div class="description">
          Upload a JSON array of products. Each product should have: id, name, description, price (in pence), and category.
        </div>
        ${this.renderProductCatalogUpload()}
        ${this.stage.productCatalog.length > 0
          ? this.renderProductCatalogPreview()
          : nothing}
      </div>

      <div class="divider"></div>

      <div class="section">
        <div class="title">AI assistant configuration</div>
        ${this.renderApiTypeSelector()}
        ${this.renderModelName()}
        ${this.renderSystemPrompt()}
        ${this.renderTemperature()}
      </div>

      <div class="divider"></div>

      <div class="section">
        <div class="title">Time limit</div>
        ${this.renderTimeLimit()}
      </div>
    `;
  }

  // ************************************************************************ //
  // SHOPPING LIST                                                            //
  // ************************************************************************ //

  private renderShoppingListItem(item: ShoppingListItem, index: number) {
    const updateName = (e: InputEvent) => {
      const name = (e.target as HTMLTextAreaElement).value;
      this.updateShoppingListItem({...item, name}, index);
    };

    const updateDescription = (e: InputEvent) => {
      const description = (e.target as HTMLTextAreaElement).value;
      this.updateShoppingListItem({...item, description}, index);
    };

    const deleteItem = () => {
      this.deleteShoppingListItem(index);
    };

    return html`
      <div class="list-item">
        <div class="list-item-content">
          <md-filled-text-field
            label="Item name"
            required
            .value=${item.name}
            ?disabled=${!this.experimentEditor.canEditStages}
            @input=${updateName}
          >
          </md-filled-text-field>
          <pr-textarea-template
            label="Description (what qualifies as fulfilling this)"
            .value=${item.description}
            ?disabled=${!this.experimentEditor.canEditStages}
            variant="outlined"
            rows="2"
            @input=${updateDescription}
          >
          </pr-textarea-template>
        </div>
        <pr-icon-button
          icon="delete"
          color="error"
          padding="small"
          variant="default"
          ?disabled=${!this.experimentEditor.canEditStages}
          @click=${deleteItem}
        >
        </pr-icon-button>
      </div>
    `;
  }

  private addShoppingListItem() {
    if (!this.stage) return;
    const shoppingList = [...this.stage.shoppingList, createShoppingListItem()];
    this.experimentEditor.updateStage({...this.stage, shoppingList});
  }

  private updateShoppingListItem(item: ShoppingListItem, index: number) {
    if (!this.stage) return;
    const shoppingList = [
      ...this.stage.shoppingList.slice(0, index),
      item,
      ...this.stage.shoppingList.slice(index + 1),
    ];
    this.experimentEditor.updateStage({...this.stage, shoppingList});
  }

  private deleteShoppingListItem(index: number) {
    if (!this.stage) return;
    const shoppingList = [
      ...this.stage.shoppingList.slice(0, index),
      ...this.stage.shoppingList.slice(index + 1),
    ];
    this.experimentEditor.updateStage({...this.stage, shoppingList});
  }

  // ************************************************************************ //
  // PRODUCT CATALOG                                                          //
  // ************************************************************************ //

  private renderProductCatalogUpload() {
    return html`
      <div class="json-upload">
        <pr-textarea-template
          label="Paste product catalog JSON"
          placeholder='[{"id": "prod-001", "name": "Product Name", "description": "Description", "price": 999, "category": "Category"}]'
          .value=${this.productCatalogJson}
          ?disabled=${!this.experimentEditor.canEditStages}
          variant="outlined"
          rows="6"
          @input=${this.handleJsonInput}
        >
        </pr-textarea-template>
        ${this.jsonError
          ? html`<div class="error-message">${this.jsonError}</div>`
          : nothing}
        <pr-button
          color="primary"
          variant="tonal"
          ?disabled=${!this.experimentEditor.canEditStages || !this.productCatalogJson}
          @click=${this.parseAndSaveProducts}
        >
          Import products
        </pr-button>
      </div>
    `;
  }

  private handleJsonInput(e: InputEvent) {
    this.productCatalogJson = (e.target as HTMLTextAreaElement).value;
    this.jsonError = null;
  }

  private parseAndSaveProducts() {
    if (!this.stage) return;

    try {
      const parsed = JSON.parse(this.productCatalogJson);

      if (!Array.isArray(parsed)) {
        this.jsonError = 'JSON must be an array of products';
        return;
      }

      const products: Product[] = [];
      for (let i = 0; i < parsed.length; i++) {
        const p = parsed[i];
        if (!p.id || typeof p.id !== 'string') {
          this.jsonError = `Product at index ${i} missing valid "id" field`;
          return;
        }
        if (!p.name || typeof p.name !== 'string') {
          this.jsonError = `Product at index ${i} missing valid "name" field`;
          return;
        }
        if (typeof p.price !== 'number' || p.price < 0) {
          this.jsonError = `Product at index ${i} missing valid "price" field (must be non-negative number)`;
          return;
        }
        products.push({
          id: p.id,
          name: p.name,
          description: p.description || '',
          price: p.price,
          category: p.category || '',
        });
      }

      this.experimentEditor.updateStage({
        ...this.stage,
        productCatalog: products,
      });
      this.productCatalogJson = '';
      this.jsonError = null;
    } catch (e) {
      this.jsonError = `Invalid JSON: ${(e as Error).message}`;
    }
  }

  private renderProductCatalogPreview() {
    if (!this.stage) return nothing;

    const clearCatalog = () => {
      if (!this.stage) return;
      this.experimentEditor.updateStage({
        ...this.stage,
        productCatalog: [],
      });
    };

    return html`
      <div class="catalog-preview">
        <div class="catalog-header">
          <span>${this.stage.productCatalog.length} products loaded</span>
          <pr-button
            color="error"
            variant="outlined"
            size="small"
            ?disabled=${!this.experimentEditor.canEditStages}
            @click=${clearCatalog}
          >
            Clear catalog
          </pr-button>
        </div>
        <div class="catalog-table">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Price</th>
                <th>Category</th>
              </tr>
            </thead>
            <tbody>
              ${this.stage.productCatalog.slice(0, 10).map(
                (p) => html`
                  <tr>
                    <td>${p.id}</td>
                    <td>${p.name}</td>
                    <td>£${(p.price / 100).toFixed(2)}</td>
                    <td>${p.category}</td>
                  </tr>
                `,
              )}
              ${this.stage.productCatalog.length > 10
                ? html`
                    <tr>
                      <td colspan="4" class="more-rows">
                        ... and ${this.stage.productCatalog.length - 10} more
                      </td>
                    </tr>
                  `
                : nothing}
            </tbody>
          </table>
        </div>
      </div>
    `;
  }

  // ************************************************************************ //
  // AI CONFIGURATION                                                         //
  // ************************************************************************ //

  private renderApiTypeSelector() {
    if (!this.stage) return nothing;

    const renderButton = (label: string, apiType: ApiKeyType) => {
      const isActive = this.stage?.assistantConfig.apiType === apiType;
      const onClick = () => {
        if (!this.stage) return;
        this.experimentEditor.updateStage({
          ...this.stage,
          assistantConfig: {...this.stage.assistantConfig, apiType},
        });
      };

      return html`
        <pr-button
          color="${isActive ? 'primary' : 'neutral'}"
          variant=${isActive ? 'tonal' : 'default'}
          ?disabled=${!this.experimentEditor.canEditStages}
          @click=${onClick}
        >
          ${label}
        </pr-button>
      `;
    };

    return html`
      <div class="config-field">
        <div class="field-label">LLM API</div>
        <div class="api-buttons">
          ${renderButton('Gemini', ApiKeyType.GEMINI_API_KEY)}
          ${renderButton('OpenAI or compatible', ApiKeyType.OPENAI_API_KEY)}
          ${renderButton('Claude or compatible', ApiKeyType.CLAUDE_API_KEY)}
          ${renderButton('Ollama Server', ApiKeyType.OLLAMA_CUSTOM_URL)}
        </div>
      </div>
    `;
  }

  private renderModelName() {
    if (!this.stage) return nothing;

    const updateModel = (e: InputEvent) => {
      if (!this.stage) return;
      const modelName = (e.target as HTMLTextAreaElement).value;
      this.experimentEditor.updateStage({
        ...this.stage,
        assistantConfig: {...this.stage.assistantConfig, modelName},
      });
    };

    return html`
      <md-filled-text-field
        label="Model ID"
        required
        .value=${this.stage.assistantConfig.modelName}
        ?disabled=${!this.experimentEditor.canEditStages}
        @input=${updateModel}
      >
      </md-filled-text-field>
    `;
  }

  private renderSystemPrompt() {
    if (!this.stage) return nothing;

    const updatePrompt = (e: InputEvent) => {
      if (!this.stage) return;
      const systemPrompt = (e.target as HTMLTextAreaElement).value;
      this.experimentEditor.updateStage({
        ...this.stage,
        assistantConfig: {...this.stage.assistantConfig, systemPrompt},
      });
    };

    return html`
      <pr-textarea-template
        label="System prompt"
        .value=${this.stage.assistantConfig.systemPrompt}
        ?disabled=${!this.experimentEditor.canEditStages}
        variant="outlined"
        rows="8"
        @input=${updatePrompt}
      >
      </pr-textarea-template>
      <div class="prompt-hint">
        This prompt will be sent directly to the AI without any experiment context.
        The AI should believe it is a real shopping assistant.
      </div>
    `;
  }

  private renderTemperature() {
    if (!this.stage) return nothing;

    const updateTemperature = (e: InputEvent) => {
      if (!this.stage) return;
      const temperature = parseFloat((e.target as HTMLInputElement).value);
      this.experimentEditor.updateStage({
        ...this.stage,
        assistantConfig: {...this.stage.assistantConfig, temperature},
      });
    };

    return html`
      <div class="config-field">
        <div class="field-label">
          Temperature: ${this.stage.assistantConfig.temperature.toFixed(1)}
        </div>
        <input
          type="range"
          min="0"
          max="2"
          step="0.1"
          .value=${this.stage.assistantConfig.temperature.toString()}
          ?disabled=${!this.experimentEditor.canEditStages}
          @input=${updateTemperature}
        />
      </div>
    `;
  }

  // ************************************************************************ //
  // TIME LIMIT                                                               //
  // ************************************************************************ //

  private renderTimeLimit() {
    if (!this.stage) return nothing;

    const timeLimit = this.stage.timeLimitInMinutes;

    const updateCheck = () => {
      if (!this.stage) return;
      this.experimentEditor.updateStage({
        ...this.stage,
        timeLimitInMinutes: timeLimit !== null ? null : 10,
      });
    };

    const updateNum = (e: InputEvent) => {
      if (!this.stage) return;
      const value = Number((e.target as HTMLInputElement).value);
      this.experimentEditor.updateStage({
        ...this.stage,
        timeLimitInMinutes: Math.max(1, value),
      });
    };

    return html`
      <div class="config-item">
        <div class="checkbox-wrapper">
          <md-checkbox
            touch-target="wrapper"
            ?checked=${timeLimit !== null}
            ?disabled=${!this.experimentEditor.canEditStages}
            @click=${updateCheck}
          >
          </md-checkbox>
          <div>Enable time limit for shopping task</div>
        </div>
        ${timeLimit !== null
          ? html`
              <div class="number-input tab">
                <label for="timeLimit">Time limit (in minutes)</label>
                <input
                  type="number"
                  id="timeLimit"
                  name="timeLimit"
                  min="1"
                  .value=${timeLimit}
                  ?disabled=${!this.experimentEditor.canEditStages}
                  @input=${updateNum}
                />
              </div>
            `
          : nothing}
      </div>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'assistant-shopping-editor': AssistantShoppingEditor;
  }
}
