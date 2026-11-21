interface FilterPillProps {
  on: boolean;
  onClick: () => void;
  children: React.ReactNode;
}

export default function FilterPill({ on, onClick, children }: FilterPillProps) {
  return (
    <button type="button" className={`pill${on ? " pill--on" : ""}`} aria-pressed={on} onClick={onClick}>
      {children}
    </button>
  );
}
