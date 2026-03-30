import type {
  ContentBlock,
  ThoughtBlock,
  TextBlock,
  ToolCallBlock,
  ToolResultBlock,
  ActionBlock,
  TerminalBlock,
  SearchBlock,
  VisualizationBlock,
  ConfirmationBlock,
  SandboxBlock,
  KbRetrievalBlock,
  MediaBlock,
  ImageBlock,
  ResourceBlock,
  ErrorBlock,
  ReferencesBlock,
  SoloLayoutBlock
} from '../types';

/**
 * Type guards for Discriminated Unions in ContentBlock.
 * These functions ensure 100% type safety and allow TypeScript to narrow down
 * the specific block type based on the 'type' property.
 */

export const isThoughtBlock = (block: ContentBlock): block is ThoughtBlock => {
  return block.type === 'thought';
};

export const isTextBlock = (block: ContentBlock): block is TextBlock => {
  return block.type === 'text';
};

export const isToolCallBlock = (block: ContentBlock): block is ToolCallBlock => {
  return block.type === 'tool_call';
};

export const isToolResultBlock = (block: ContentBlock): block is ToolResultBlock => {
  return block.type === 'tool_result';
};

export const isActionBlock = (block: ContentBlock): block is ActionBlock => {
  return block.type === 'action';
};

export const isTerminalBlock = (block: ContentBlock): block is TerminalBlock => {
  return block.type === 'terminal';
};

export const isSearchBlock = (block: ContentBlock): block is SearchBlock => {
  return block.type === 'search';
};

export const isVisualizationBlock = (block: ContentBlock): block is VisualizationBlock => {
  return block.type === 'visualization';
};

export const isConfirmationBlock = (block: ContentBlock): block is ConfirmationBlock => {
  return block.type === 'confirmation';
};

export const isSandboxBlock = (block: ContentBlock): block is SandboxBlock => {
  return block.type === 'sandbox';
};

export const isKbRetrievalBlock = (block: ContentBlock): block is KbRetrievalBlock => {
  return block.type === 'kb_retrieval';
};

export const isMediaBlock = (block: ContentBlock): block is MediaBlock => {
  return block.type === 'media';
};

export const isImageBlock = (block: ContentBlock): block is ImageBlock => {
  return block.type === 'image';
};

export const isResourceBlock = (block: ContentBlock): block is ResourceBlock => {
  return block.type === 'resource';
};

export const isErrorBlock = (block: ContentBlock): block is ErrorBlock => {
  return block.type === 'error';
};

export const isReferencesBlock = (block: ContentBlock): block is ReferencesBlock => {
  return block.type === 'references';
};

export const isSoloLayoutBlock = (block: ContentBlock): block is SoloLayoutBlock => {
  return block.type === 'solo_layout';
};
