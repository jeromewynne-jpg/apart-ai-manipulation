import {Value} from '@sinclair/typebox/value';
import {Timestamp} from 'firebase-admin/firestore';
import {onCall, HttpsError} from 'firebase-functions/v2/https';

import {
  StageKind,
  AssistantShoppingStageConfig,
  AssistantShoppingStageParticipantAnswer,
  ShoppingChatMessage,
  ProductRecommendation,
  BasketItem,
  BasketAction,
  createAssistantShoppingParticipantAnswer,
  SendShoppingMessageData,
  UpdateBasketData,
  createModelGenerationConfig,
  APIKeyConfig,
} from '@deliberation-lab/utils';

import {app} from '../app';
import {
  getFirestoreStage,
  getFirestoreParticipantAnswer,
  getExperimenterDataFromExperiment,
} from '../utils/firestore';
import {generateAIResponse, ModelMessage} from '../api/ai-sdk.api';

// ************************************************************************* //
// HELPER FUNCTIONS                                                          //
// ************************************************************************* //

/** Get or create participant answer for Assistant Shopping stage. */
async function getOrCreateParticipantAnswer(
  experimentId: string,
  participantPrivateId: string,
  stageId: string,
): Promise<AssistantShoppingStageParticipantAnswer> {
  const existingAnswer = await getFirestoreParticipantAnswer(
    experimentId,
    participantPrivateId,
    stageId,
  );

  if (
    existingAnswer &&
    existingAnswer.kind === StageKind.ASSISTANT_SHOPPING
  ) {
    return existingAnswer as AssistantShoppingStageParticipantAnswer;
  }

  return createAssistantShoppingParticipantAnswer(stageId);
}

/** Save participant answer to Firestore. */
async function saveParticipantAnswer(
  experimentId: string,
  participantPrivateId: string,
  answer: AssistantShoppingStageParticipantAnswer,
) {
  const ref = app
    .firestore()
    .collection('experiments')
    .doc(experimentId)
    .collection('participants')
    .doc(participantPrivateId)
    .collection('stageData')
    .doc(answer.id);

  await ref.set(answer);
}

/** Build the product catalog context for the AI system prompt. */
function buildProductCatalogContext(
  stage: AssistantShoppingStageConfig,
): string {
  const products = stage.productCatalog
    .map(
      (p) =>
        `- ID: ${p.id} | ${p.name} | £${(p.price / 100).toFixed(2)} | ${p.category} | ${p.description}`,
    )
    .join('\n');

  return `
AVAILABLE PRODUCTS:
${products}

IMPORTANT INSTRUCTIONS FOR RECOMMENDATIONS:
- When you want to recommend a product, include a tag in your response: [RECOMMEND:product_id:brief reason]
- The tag will be converted into a product card showing the name and price to the customer.
- DO NOT repeat the product name, ID, or price in your text - the card will display this information.
- Just write a natural conversational response explaining why the product might suit their needs.
- You can recommend multiple products by including multiple [RECOMMEND:...] tags.

Example response:
"Based on what you've told me, I think these would work really well for your TV remote - they're known for lasting a long time in low-drain devices. [RECOMMEND:bat-001:Long-lasting for remotes]"

The customer will see your text plus a product card. Do NOT write things like "I recommend the Duracell AA Batteries (4-pack) priced at £5.99" - just use the tag and write naturally about why the product suits their needs.
`;
}

/** Parse [RECOMMEND:product_id:reason] tags from response text. */
function parseProductRecommendations(
  text: string,
  productCatalog: {id: string}[],
): {recommendations: ProductRecommendation[]; cleanedText: string} {
  const recommendations: ProductRecommendation[] = [];
  const tagPattern = /\[RECOMMEND:([^:\]]+):([^\]]+)\]/g;

  let match;
  while ((match = tagPattern.exec(text)) !== null) {
    const productId = match[1].trim();
    const reason = match[2].trim();

    // Validate product exists
    const productExists = productCatalog.some((p) => p.id === productId);
    if (productExists) {
      recommendations.push({productId, reason});
    }
  }

  // Remove the tags from the displayed text
  const cleanedText = text.replace(tagPattern, '').trim();

  return {recommendations, cleanedText};
}

/** Convert chat history to AI SDK message format. */
function buildMessageHistory(
  chatHistory: ShoppingChatMessage[],
): ModelMessage[] {
  return chatHistory.map((msg) => ({
    role: msg.role as 'user' | 'assistant',
    content: msg.content,
  }));
}

// ************************************************************************* //
// sendAssistantShoppingMessage endpoint                                     //
//                                                                           //
// Sends a message to the AI shopping assistant and returns the response.    //
// ************************************************************************* //

export const sendAssistantShoppingMessage = onCall(async (request) => {
  const {data} = request;

  // Validate input
  if (!Value.Check(SendShoppingMessageData, data)) {
    throw new HttpsError('invalid-argument', 'Invalid request data');
  }

  const {experimentId, participantPrivateId, stageId, message} = data;

  // Get experimenter data for API keys
  const experimenterData = await getExperimenterDataFromExperiment(experimentId);
  if (!experimenterData) {
    throw new HttpsError('not-found', `Experimenter data for experiment ${experimentId} not found`);
  }

  // Get stage config
  const stage = await getFirestoreStage(experimentId, stageId);
  if (!stage || stage.kind !== StageKind.ASSISTANT_SHOPPING) {
    throw new HttpsError(
      'not-found',
      `Assistant Shopping stage ${stageId} not found`,
    );
  }

  const shoppingStage = stage as AssistantShoppingStageConfig;

  // Get or create participant answer
  let participantAnswer = await getOrCreateParticipantAnswer(
    experimentId,
    participantPrivateId,
    stageId,
  );

  // Set start time if this is the first message
  if (!participantAnswer.startedAt) {
    participantAnswer = {
      ...participantAnswer,
      startedAt: Timestamp.now(),
    };
  }

  // Add user message to history
  const userMessage: ShoppingChatMessage = {
    id: `msg-${Date.now()}-user`,
    role: 'user',
    content: message,
    timestamp: Timestamp.now(),
  };

  const updatedChatHistory = [...participantAnswer.chatHistory, userMessage];

  // Build the full prompt with system message
  const systemPrompt = `${shoppingStage.assistantConfig.systemPrompt}

${buildProductCatalogContext(shoppingStage)}`;

  const messages: ModelMessage[] = [
    {role: 'system', content: systemPrompt},
    ...buildMessageHistory(updatedChatHistory),
  ];

  // Call the AI using generateAIResponse
  const apiKeyConfig: APIKeyConfig = experimenterData.apiKeys || {};
  const modelSettings = {
    apiType: shoppingStage.assistantConfig.apiType,
    modelName: shoppingStage.assistantConfig.modelName,
  };
  const generationConfig = createModelGenerationConfig({
    temperature: shoppingStage.assistantConfig.temperature,
    maxTokens: 2048,
  });

  const response = await generateAIResponse(
    apiKeyConfig,
    messages,
    modelSettings,
    generationConfig,
  );

  if (!response.text) {
    throw new HttpsError('internal', 'Failed to generate AI response');
  }

  // Parse [RECOMMEND:...] tags from response and get cleaned text
  const {recommendations: productRecommendations, cleanedText} =
    parseProductRecommendations(response.text, shoppingStage.productCatalog);

  // Create assistant message with cleaned text (tags removed)
  const assistantMessage: ShoppingChatMessage = {
    id: `msg-${Date.now()}-assistant`,
    role: 'assistant',
    content: cleanedText,
    timestamp: Timestamp.now(),
    productRecommendations:
      productRecommendations.length > 0 ? productRecommendations : undefined,
  };

  // Update participant answer with new messages
  participantAnswer = {
    ...participantAnswer,
    chatHistory: [...updatedChatHistory, assistantMessage],
  };

  // Save to Firestore
  await saveParticipantAnswer(experimentId, participantPrivateId, participantAnswer);

  return {
    message: assistantMessage,
    productRecommendations,
  };
});

// ************************************************************************* //
// updateAssistantShoppingBasket endpoint                                    //
//                                                                           //
// Adds or removes a product from the participant's basket.                  //
// ************************************************************************* //

export const updateAssistantShoppingBasket = onCall(async (request) => {
  const {data} = request;

  // Validate input
  if (!Value.Check(UpdateBasketData, data)) {
    throw new HttpsError('invalid-argument', 'Invalid request data');
  }

  const {experimentId, participantPrivateId, stageId, action, productId} = data;

  // Get stage config to validate product exists
  const stage = await getFirestoreStage(experimentId, stageId);
  if (!stage || stage.kind !== StageKind.ASSISTANT_SHOPPING) {
    throw new HttpsError(
      'not-found',
      `Assistant Shopping stage ${stageId} not found`,
    );
  }

  const shoppingStage = stage as AssistantShoppingStageConfig;

  // Validate product exists in catalog
  const product = shoppingStage.productCatalog.find((p) => p.id === productId);
  if (!product) {
    throw new HttpsError('not-found', `Product ${productId} not found`);
  }

  // Get or create participant answer
  let participantAnswer = await getOrCreateParticipantAnswer(
    experimentId,
    participantPrivateId,
    stageId,
  );

  const timestamp = Timestamp.now();

  // Create basket action for history
  const basketAction: BasketAction = {
    type: action,
    productId,
    timestamp,
  };

  // Update basket based on action
  let updatedBasket = [...participantAnswer.basket];

  if (action === 'add') {
    // Check if product is already in basket
    const existingItem = updatedBasket.find(
      (item) => item.productId === productId,
    );
    if (!existingItem) {
      const basketItem: BasketItem = {
        productId,
        addedAt: timestamp,
      };
      updatedBasket.push(basketItem);
    }
  } else if (action === 'remove') {
    updatedBasket = updatedBasket.filter(
      (item) => item.productId !== productId,
    );
  }

  // Update participant answer
  participantAnswer = {
    ...participantAnswer,
    basket: updatedBasket,
    basketHistory: [...participantAnswer.basketHistory, basketAction],
  };

  // Save to Firestore
  await saveParticipantAnswer(experimentId, participantPrivateId, participantAnswer);

  return {
    basket: updatedBasket,
    action: basketAction,
  };
});
