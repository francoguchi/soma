import type {ButtonHTMLAttributes, ReactNode} from 'react';
import {SomaIcon, type IconName} from './SomaIcon';
export function SectionHeading({icon, children, actions, level = 2}: {icon: IconName; children: ReactNode; actions?: ReactNode; level?: 2 | 3}) {
  const Heading = level === 2 ? 'h2' : 'h3';
  return <div className="section-heading"><Heading><SomaIcon name={icon}/>{children}</Heading>{actions}</div>;
}
export function ConsoleComment({children}: {children: ReactNode}) {return <p className="console-comment"><span aria-hidden="true">//</span> {children}</p>;}
export function FormActions({children}: {children: ReactNode}) {return <div className="form-actions">{children}</div>;}
export function Action({icon, variant = 'quiet', children, className = '', type = 'button', ...props}: ButtonHTMLAttributes<HTMLButtonElement> & {icon?: IconName; variant?: 'command' | 'quiet' | 'destructive'}) {
  return <button {...props} type={type} className={`soma-action action-${variant} ${className}`}>{icon && <SomaIcon name={icon}/>} {children}</button>;
}
export function SectionTabs({label, items, current, navigate, secondary = false}: {label: string; items: readonly {href: string; title: string}[]; current: string; navigate: (href: string) => void; secondary?: boolean}) {
  return <nav aria-label={label} className="section-tabs" data-level={secondary ? 'secondary' : 'primary'}>{items.map(item => <a key={item.href} href={item.href} aria-current={item.href === current ? 'page' : undefined} onClick={event => {if (event.button === 0 && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey) {event.preventDefault(); navigate(item.href);}}}>{item.title}</a>)}</nav>;
}
