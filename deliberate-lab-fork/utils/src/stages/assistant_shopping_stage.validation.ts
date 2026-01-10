import {Type, type Static} from '@sinclair/typebox';
import {UnifiedTimestampSchema} from '../shared.validation';
import {StageKind} from './stage';
import {
  StageTextConfigSchema,
  StageProgressConfigSchema,
} from './stage.validation';
import {ApiKeyType} from '../providers';

/** Shorthand for strict TypeBox object validation */
const strict = {additionalProperties: false} as const;

// ************************************************************************* //
// STAGE CONFIG VALIDATION                                                   //
// ************************************************************************* //

/** ShoppingListItem validation schema. */
export const ShoppingListItemSchema = Type.Object(
  {
    id: Type.String({minLength: 1}),
    name: Type.String(),
    description: Type.String(),
  },
  {$id: 'ShoppingListItem', ...strict},
);

/** Product validation schema. */
export const ProductSchema = Type.Object(
  {
    id: Type.String({minLength: 1}),
    name: Type.String(),
    description: Type.String(),
    price: Type.Number({minimum: 0}),
    category: Type.String(),
  },
  {$id: 'Product', ...strict},
);

/** ApiKeyType validation. */
export const ApiKeyTypeSchema = Type.Union([
  Type.Literal(ApiKeyType.GEMINI_API_KEY),
  Type.Literal(ApiKeyType.OPENAI_API_KEY),
  Type.Literal(ApiKeyType.CLAUDE_API_KEY),
  Type.Literal(ApiKeyType.OLLAMA_CUSTOM_URL),
]);

/** AssistantConfig validation schema. */
export const AssistantConfigSchema = Type.Object(
  {
    apiType: ApiKeyTypeSchema,
    modelName: Type.String({minLength: 1}),
    systemPrompt: Type.String(),
    temperature: Type.Number({minimum: 0, maximum: 2}),
  },
  {$id: 'AssistantConfig', ...strict},
);

/** AssistantShoppingStageConfig validation schema. */
export const AssistantShoppingStageConfigData = Type.Object(
  {
    id: Type.String({minLength: 1}),
    kind: Type.Literal(StageKind.ASSISTANT_SHOPPING),
    name: Type.String(),
    descriptions: Type.Ref(StageTextConfigSchema),
    progress: Type.Ref(StageProgressConfigSchema),
    shoppingList: Type.Array(ShoppingListItemSchema),
    productCatalog: Type.Array(ProductSchema),
    assistantConfig: AssistantConfigSchema,
    timeLimitInMinutes: Type.Union([Type.Number({minimum: 1}), Type.Null()]),
  },
  {$id: 'AssistantShoppingStageConfig', ...strict},
);

export type AssistantShoppingStageConfigData = Static<
  typeof AssistantShoppingStageConfigData
>;

// ************************************************************************* //
// PARTICIPANT ANSWER VALIDATION                                             //
// ************************************************************************* //

/** BasketItem validation schema. */
export const BasketItemSchema = Type.Object(
  {
    productId: Type.String({minLength: 1}),
    addedAt: UnifiedTimestampSchema,
  },
  {$id: 'BasketItem', ...strict},
);

/** BasketAction validation schema. */
export const BasketActionSchema = Type.Object(
  {
    type: Type.Union([Type.Literal('add'), Type.Literal('remove')]),
    productId: Type.String({minLength: 1}),
    timestamp: UnifiedTimestampSchema,
  },
  {$id: 'BasketAction', ...strict},
);

/** ProductRecommendation validation schema. */
export const ProductRecommendationSchema = Type.Object(
  {
    productId: Type.String({minLength: 1}),
    reason: Type.String(),
  },
  {$id: 'ProductRecommendation', ...strict},
);

/** ShoppingChatMessage validation schema. */
export const ShoppingChatMessageSchema = Type.Object(
  {
    id: Type.String({minLength: 1}),
    role: Type.Union([Type.Literal('user'), Type.Literal('assistant')]),
    content: Type.String(),
    timestamp: UnifiedTimestampSchema,
    productRecommendations: Type.Optional(
      Type.Array(ProductRecommendationSchema),
    ),
  },
  {$id: 'ShoppingChatMessage', ...strict},
);

/** AssistantShoppingStageParticipantAnswer validation schema. */
export const AssistantShoppingStageParticipantAnswerData = Type.Object(
  {
    id: Type.String({minLength: 1}),
    kind: Type.Literal(StageKind.ASSISTANT_SHOPPING),
    basket: Type.Array(BasketItemSchema),
    basketHistory: Type.Array(BasketActionSchema),
    chatHistory: Type.Array(ShoppingChatMessageSchema),
    startedAt: Type.Union([UnifiedTimestampSchema, Type.Null()]),
    completedAt: Type.Union([UnifiedTimestampSchema, Type.Null()]),
  },
  {$id: 'AssistantShoppingStageParticipantAnswer', ...strict},
);

export type AssistantShoppingStageParticipantAnswerData = Static<
  typeof AssistantShoppingStageParticipantAnswerData
>;

// ************************************************************************* //
// ENDPOINT VALIDATION                                                       //
// ************************************************************************* //

/** SendShoppingMessage endpoint validation. */
export const SendShoppingMessageData = Type.Object(
  {
    experimentId: Type.String({minLength: 1}),
    participantPrivateId: Type.String({minLength: 1}),
    stageId: Type.String({minLength: 1}),
    message: Type.String({minLength: 1}),
  },
  strict,
);

export type SendShoppingMessageData = Static<typeof SendShoppingMessageData>;

/** UpdateBasket endpoint validation. */
export const UpdateBasketData = Type.Object(
  {
    experimentId: Type.String({minLength: 1}),
    participantPrivateId: Type.String({minLength: 1}),
    stageId: Type.String({minLength: 1}),
    action: Type.Union([Type.Literal('add'), Type.Literal('remove')]),
    productId: Type.String({minLength: 1}),
  },
  strict,
);

export type UpdateBasketData = Static<typeof UpdateBasketData>;
