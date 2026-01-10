import {generateId, UnifiedTimestamp} from '../shared';
import {ApiKeyType} from '../providers';
import {
  BaseStageConfig,
  BaseStageParticipantAnswer,
  StageKind,
  createStageTextConfig,
  createStageProgressConfig,
} from './stage';

/**
 * Assistant Shopping Stage
 *
 * A stage where participants interact with an AI shopping assistant
 * to complete a shopping task. The AI makes direct API calls with
 * a clean system prompt (no experiment context).
 */

// ************************************************************************* //
// STAGE CONFIG TYPES                                                        //
// ************************************************************************* //

/** Shopping list item that participant must purchase. */
export interface ShoppingListItem {
  id: string;
  name: string; // e.g., "AA Batteries (4-pack)"
  description: string; // What qualifies as fulfilling this item
}

/** Product in the catalog. */
export interface Product {
  id: string;
  name: string;
  description: string;
  price: number; // in pence (integer to avoid float issues)
  category: string;
}

/** AI assistant configuration (direct API, not mediator). */
export interface AssistantConfig {
  apiType: ApiKeyType;
  modelName: string;
  systemPrompt: string; // Clean prompt with no experiment context
  temperature: number;
}

/** Assistant Shopping stage configuration. */
export interface AssistantShoppingStageConfig extends BaseStageConfig {
  kind: StageKind.ASSISTANT_SHOPPING;
  shoppingList: ShoppingListItem[];
  productCatalog: Product[];
  assistantConfig: AssistantConfig;
  timeLimitInMinutes: number | null;
}

// ************************************************************************* //
// PARTICIPANT ANSWER TYPES                                                  //
// ************************************************************************* //

/** Item currently in the basket. */
export interface BasketItem {
  productId: string;
  addedAt: UnifiedTimestamp;
}

/** Basket action for analytics logging. */
export interface BasketAction {
  type: 'add' | 'remove';
  productId: string;
  timestamp: UnifiedTimestamp;
}

/** Chat message in the shopping conversation. */
export interface ShoppingChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: UnifiedTimestamp;
  // Product recommendations from AI tool calls
  productRecommendations?: ProductRecommendation[];
}

/** Product recommendation from AI tool call. */
export interface ProductRecommendation {
  productId: string;
  reason: string;
}

/** Participant's answer/state for the Assistant Shopping stage. */
export interface AssistantShoppingStageParticipantAnswer
  extends BaseStageParticipantAnswer {
  kind: StageKind.ASSISTANT_SHOPPING;
  basket: BasketItem[];
  basketHistory: BasketAction[];
  chatHistory: ShoppingChatMessage[];
  startedAt: UnifiedTimestamp | null;
  completedAt: UnifiedTimestamp | null;
}

// ************************************************************************* //
// FACTORY FUNCTIONS                                                         //
// ************************************************************************* //

/** Create default assistant config. */
export function createAssistantConfig(
  config: Partial<AssistantConfig> = {},
): AssistantConfig {
  return {
    apiType: config.apiType ?? ApiKeyType.GEMINI_API_KEY,
    modelName: config.modelName ?? 'gemini-2.0-flash',
    systemPrompt:
      config.systemPrompt ??
      'You are a helpful shopping assistant. Help customers find products that meet their needs.',
    temperature: config.temperature ?? 0.7,
  };
}

/** Create a shopping list item. */
export function createShoppingListItem(
  config: Partial<ShoppingListItem> = {},
): ShoppingListItem {
  return {
    id: config.id ?? generateId(),
    name: config.name ?? '',
    description: config.description ?? '',
  };
}

/** Create a product. */
export function createProduct(config: Partial<Product> = {}): Product {
  return {
    id: config.id ?? generateId(),
    name: config.name ?? '',
    description: config.description ?? '',
    price: config.price ?? 0,
    category: config.category ?? '',
  };
}

/** Create Assistant Shopping stage config. */
export function createAssistantShoppingStage(
  config: Partial<AssistantShoppingStageConfig> = {},
): AssistantShoppingStageConfig {
  return {
    id: config.id ?? generateId(),
    kind: StageKind.ASSISTANT_SHOPPING,
    name: config.name ?? 'Shopping Task',
    descriptions: config.descriptions ?? createStageTextConfig(),
    progress:
      config.progress ??
      createStageProgressConfig({waitForAllParticipants: false}),
    shoppingList: config.shoppingList ?? [],
    productCatalog: config.productCatalog ?? [],
    assistantConfig: config.assistantConfig ?? createAssistantConfig(),
    timeLimitInMinutes: config.timeLimitInMinutes ?? 10,
  };
}

/** Create initial participant answer for Assistant Shopping stage. */
export function createAssistantShoppingParticipantAnswer(
  stageId: string,
): AssistantShoppingStageParticipantAnswer {
  return {
    id: stageId,
    kind: StageKind.ASSISTANT_SHOPPING,
    basket: [],
    basketHistory: [],
    chatHistory: [],
    startedAt: null,
    completedAt: null,
  };
}

// ************************************************************************* //
// HELPER FUNCTIONS                                                          //
// ************************************************************************* //

/** Calculate total basket cost in pence. */
export function calculateBasketTotal(
  basket: BasketItem[],
  productCatalog: Product[],
): number {
  return basket.reduce((total, item) => {
    const product = productCatalog.find((p) => p.id === item.productId);
    return total + (product?.price ?? 0);
  }, 0);
}

/** Format price from pence to display string (e.g., "£5.99"). */
export function formatPrice(priceInPence: number): string {
  return `£${(priceInPence / 100).toFixed(2)}`;
}

/** Check if a product is in the basket. */
export function isProductInBasket(
  productId: string,
  basket: BasketItem[],
): boolean {
  return basket.some((item) => item.productId === productId);
}
