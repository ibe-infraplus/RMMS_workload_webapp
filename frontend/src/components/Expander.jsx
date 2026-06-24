import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

export default function Expander({ title, children, defaultOpen = false }) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  return (
    <div className="expander">
      <div className="expander-header" onClick={() => setIsOpen(!isOpen)}>
        <span className="expander-title">{title}</span>
        {isOpen ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
      </div>
      {isOpen && <div className="expander-content">{children}</div>}
    </div>
  );
}
