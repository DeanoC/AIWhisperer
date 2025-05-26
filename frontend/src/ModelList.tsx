import React from 'react';
import './ModelList.css';

const models = [
  'openai/codex-mini',
  'meta-llama/llama-3-3.8b-instruct:free',
  'nousresearch/deepm...-mistral-24b',
  'mistralai/mistral-medium-3',
  'google/gemini-2.5-pro-preview',
  'arcee-ai/caller-large',
  'arcee-ai/spotlight',
  'arcee-ai/maestro-reasoning',
  'arcee-ai/virtuoso-large',
  'arcee-ai/coder-large',
  'arcee-ai/virtuoso-medium-v2',
  'arcee-ai/arcee-blitz',
  'microsoft/phi-4-reasoning-plus:free',
  'microsoft/phi-4-reasoning:free',
  'microsoft/phi-4-reasoning',
  'qwen/qwen3-0.6b-04-28:free',
  'inception/mercury-coder-small-beta',
  'qwen/qwen3-1.7b:free',
  'qwen/qwen3-4b:free',
  'opengvlab/internvl3-14b:free',
  'opengvlab/internvl3-2b:free',
  'deepseek/deepseek-prover-v2:free',
  'deepseek/deepseek-prover-v2',
  'meta-llama/llama-guard-4-12b',
  'qwen/qwen3-30b-a3b:free',
  'qwen/qwen3-8b:free',
  'qwen/qwen3-14b:free',
  'qwen/qwen3-32b',
  'qwen/qwen3-235b-a22b:free',
  'thudm/glm-z1-9b:free',
  'thudm/glm-4-9b:free',
  'microsoft/mai-ds-rl:free',
  'thudm/glm-z1-32b:free',
  'thudm/glm-4-32b:free',
];

interface ModelListProps {
  selected: string;
  onSelect: (model: string) => void;
}

const ModelList: React.FC<ModelListProps> = ({ selected, onSelect }) => (
  <div className="model-list">
    {models.map((model) => (
      <div
        key={model}
        className={`model-item${selected === model ? ' selected' : ''}`}
        onClick={() => onSelect(model)}
      >
        {model}
      </div>
    ))}
  </div>
);

export default ModelList;
