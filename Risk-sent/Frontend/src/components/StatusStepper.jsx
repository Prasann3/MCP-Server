import React, { Fragment } from 'react';
import { Check, Search, Network, Database, Brain, CheckCircle2 } from 'lucide-react';

const steps = [
  { id: 1, label: "Analyzing", icon: Search },
  { id: 2, label: "MCP Link", icon: Network },
  { id: 3, label: "PDF Search", icon: Database },
  { id: 4, label: "Thinking", icon: Brain },
  { id: 5, label: "Done", icon: CheckCircle2 },
];

export default function StatusStepper({ currentStep }) {
  return (
    <div className="flex items-center gap-4 bg-card px-4 py-2 rounded-full border border-border shadow-sm">
      {steps.map((step, index) => {
        const Icon = step.icon;
        const isCompleted = currentStep > step.id;
        const isActive = currentStep === step.id;
        const isPending = currentStep < step.id;

        return (
          <Fragment key={step.id}>
            <div className="flex items-center gap-2">
              <div className="relative">
                {isActive && (
                  <div className="absolute inset-0 rounded-full bg-primary animate-ping opacity-75" />
                )}
                
                <div className={`
                  relative z-10 w-8 h-8 rounded-full flex items-center justify-center transition-all duration-500
                  ${isCompleted ? 'bg-green-500 text-white' : ''}
                  ${isActive ? 'bg-primary text-primary-foreground scale-110 shadow-md' : ''}
                  ${isPending ? 'bg-muted text-muted-foreground' : ''}
                `}>
                  {isCompleted ? <Check size={16} strokeWidth={3} /> : <Icon size={16} />}
                </div>
              </div>
              
              <span className={`text-xs font-semibold hidden lg:block ${isActive ? 'text-primary' : 'text-muted-foreground'}`}>
                {step.label}
              </span>
            </div>

            {index < steps.length - 1 && (
              <div className="w-6 h-[2px] bg-muted rounded-full overflow-hidden">
                <div 
                  className="h-full bg-green-500 transition-all duration-700 ease-in-out"
                  style={{ width: isCompleted ? "100%" : "0%" }}
                />
              </div>
            )}
          </Fragment>
        );
      })}
    </div>
  );
}
