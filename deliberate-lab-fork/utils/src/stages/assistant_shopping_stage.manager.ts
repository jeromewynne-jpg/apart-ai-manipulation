import {ParticipantProfileExtended} from '../participant';
import {
  MediatorPromptConfig,
  ParticipantPromptConfig,
} from '../structured_prompt';
import {AssistantShoppingStageConfig} from './assistant_shopping_stage';
import {StageConfig, StageContextData} from './stage';
import {AgentParticipantStageActions, BaseStageHandler} from './stage.handler';

/**
 * Handler for Assistant Shopping stage.
 *
 * This stage uses direct API calls to an LLM (not the mediator system),
 * so most handler methods return defaults or empty values.
 */
export class AssistantShoppingStageHandler extends BaseStageHandler {
  /**
   * Agent participants don't interact with this stage via the mediator system.
   * They would need custom handling if agent participants are desired.
   */
  getAgentParticipantActionsForStage(
    participant: ParticipantProfileExtended,
    stage: StageConfig,
  ): AgentParticipantStageActions {
    // Don't call API or auto-advance - this stage requires human interaction
    return {callApi: false, moveToNextStage: false};
  }

  /**
   * Returns stage display for prompts.
   * Since this stage uses direct API calls, we don't need to format
   * the stage for the mediator prompt system.
   */
  getStageDisplayForPrompt(
    participants: ParticipantProfileExtended[],
    stageContext: StageContextData,
    includeScaffolding: boolean,
  ): string {
    const stage = stageContext.stage as AssistantShoppingStageConfig;
    return `Shopping task: ${stage.name}`;
  }

  /**
   * No default mediator prompt - this stage uses direct API calls.
   */
  getDefaultMediatorStructuredPrompt(
    stage: AssistantShoppingStageConfig,
  ): MediatorPromptConfig | undefined {
    return undefined;
  }

  /**
   * No default participant prompt - this stage uses direct API calls.
   */
  getDefaultParticipantStructuredPrompt(
    stage: AssistantShoppingStageConfig,
  ): ParticipantPromptConfig | undefined {
    return undefined;
  }
}
