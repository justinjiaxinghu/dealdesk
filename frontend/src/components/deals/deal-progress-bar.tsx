"use client";

const STAGES = [
  { key: "upload", label: "Upload OM" },
  { key: "extract", label: "Extract Data" },
  { key: "assumptions", label: "Set Assumptions" },
  { key: "validate", label: "Validate OM" },
  { key: "export", label: "Export" },
] as const;

type StageKey = (typeof STAGES)[number]["key"];

const ACTIVE_STEP_LABELS: Record<string, string> = {
  extract: "Extracting data...",
  assumptions: "Generating benchmarks...",
  validate: "Validating OM...",
};

interface DealProgressBarProps {
  hasDocuments: boolean;
  hasFields: boolean;
  hasAssumptions: boolean;
  hasValidations: boolean;
  activeStep?: StageKey | null;
}

function getActiveStage(props: DealProgressBarProps): number {
  if (props.hasValidations) return 4;
  if (props.hasAssumptions) return 3;
  if (props.hasFields) return 2;
  if (props.hasDocuments) return 1;
  return 0;
}

function Spinner() {
  return (
    <svg
      className="w-4 h-4 animate-spin"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg
      className="w-4 h-4"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={3}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M5 13l4 4L19 7"
      />
    </svg>
  );
}

export function DealProgressBar(props: DealProgressBarProps) {
  const activeStage = getActiveStage(props);
  const { activeStep } = props;

  return (
    <div className="w-full">
      {/* Step circles + connectors */}
      <div className="flex items-center w-full">
        {STAGES.map((stage, index) => {
          const isCompleted = index < activeStage;
          const isCurrent = index === activeStage;
          const isRunning = activeStep === stage.key && !isCompleted;
          const isFuture = !isCompleted && !isCurrent;

          return (
            <div key={stage.key} className="flex items-center flex-1 last:flex-none">
              {/* Step circle + label */}
              <div className="flex flex-col items-center">
                <div
                  className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-semibold border-2 transition-all ${
                    isCompleted
                      ? "bg-green-600 border-green-600 text-white"
                      : isRunning
                        ? "bg-blue-600 border-blue-600 text-white ring-4 ring-blue-600/20"
                        : isCurrent
                          ? "bg-blue-600 border-blue-600 text-white"
                          : "bg-muted border-muted-foreground/30 text-muted-foreground"
                  }`}
                >
                  {isCompleted ? (
                    <CheckIcon />
                  ) : isRunning ? (
                    <Spinner />
                  ) : (
                    index + 1
                  )}
                </div>
                <span
                  className={`text-xs mt-1.5 whitespace-nowrap ${
                    isRunning
                      ? "text-blue-600 font-bold"
                      : isCompleted
                        ? "text-green-700 font-medium"
                        : isCurrent
                          ? "text-foreground font-semibold"
                          : "text-muted-foreground"
                  }`}
                >
                  {isRunning && ACTIVE_STEP_LABELS[stage.key]
                    ? ACTIVE_STEP_LABELS[stage.key]
                    : stage.label}
                </span>
              </div>

              {/* Connector line */}
              {index < STAGES.length - 1 && (
                <div
                  className={`h-0.5 flex-1 mx-2 ${
                    isCompleted ? "bg-green-600" : isFuture ? "bg-muted-foreground/15" : "bg-muted-foreground/25"
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
