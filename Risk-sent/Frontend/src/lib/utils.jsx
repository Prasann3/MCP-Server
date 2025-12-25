import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

export const formatGeminiText = (text) => {
  return text.split('\n').map((line, i) => {
    if (line.startsWith('###')) {
      return (<h3 key={i} className="text-xl font-bold text-foreground mt-6 mb-3 tracking-tight">{line.replace('###', '')}</h3>);
    }
    
    const parts = line.split(/(\*\*.*?\*\*)/g);
    return (
      <p key={i} className="mb-4">
        {parts.map((part, j) => {
          if (part.startsWith('**') && part.endsWith('**')) {
            return <strong key={j} className="font-bold text-primary">{part.slice(2, -2)}</strong>;
          }
          return part;
        })}
      </p>
    );
  });
};
