"use client";

const STAGES = [
  { key: "upload", label: "Upload OM" },
  { key: "extract", label: "Extract Data" },
  { key: "assumptions", label: "Set Assumptions" },
  { key: "model", label: "Compute Model" },
  { key: "export", label: "Export" },
] as const;

interface DealProgressBarProps {
  /** Current status of the deal. Maps to stage progression. */
  status: string;
  /** Whether any documents have been uploaded. */
  hasDocuments: boolean;
  /** Whether extracted fields exist. */
  hasFields: boolean;
  /** Whether assumptions exist. */
  hasAssumptions: boolean;
  /** Whether a model result exists. */
  hasModelResult: boolean;
}

function getActiveStage(props: DealProgressBarProps): number {
  if (props.hasModelResult) return 4; // export stage
  if (props.hasAssumptions) return 3; // compute model stage
  if (props.hasFields) return 2; // set assumptions stage
  if (props.hasDocuments) return 1; // extract data stage
  return 0; // upload OM stage
}

export function DealProgressBar(props: DealProgressBarProps) {
  const activeStage = getActiveStage(props);

  return (
    <div className="flex items-center gap-0 w-full">
      {STAGES.map((stage, index) => {
        const isCompleted = index < activeStage;
        const isCurrent = index === activeStage;

        return (
          <div key={stage.key} className="flex items-center flex-1">
            <div className="flex flex-col items-center flex-1">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium border-2 transition-colors ${
                  isCompleted
                    ? "bg-green-600 border-green-600 text-white"
                    : isCurrent
                      ? "bg-blue-600 border-blue-600 text-white"
                      : "bg-muted border-muted-foreground/30 text-muted-foreground"
                }`}
              >
                {isCompleted ? (
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
                ) : (
                  index + 1
                )}
              </div>
              <span
                className={`text-xs mt-1 text-center ${
                  isCurrent
                    ? "text-foreground font-semibold"
                    : "text-muted-foreground"
                }`}
              >
                {stage.label}
              </span>
            </div>
            {index < STAGES.length - 1 && (
              <div
                className={`h-0.5 flex-1 -mx-1 mt-[-1rem] ${
                  isCompleted ? "bg-green-600" : "bg-muted-foreground/20"
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
