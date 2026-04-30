import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Activity, Heart, Calendar, Link2 } from 'lucide-react';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/strava', icon: Activity, label: 'Strava' },
  { to: '/whoop', icon: Heart, label: 'Whoop' },
  { to: '/plans/active', icon: Calendar, label: 'Plan' },
  { to: '/integrations', icon: Link2, label: 'Integrations' },
];

export function Navigation() {
  return (
    <aside className="flex w-56 shrink-0 flex-col border-r border-grunge-charcoal bg-grunge-black/95 px-3 py-6">
      <div className="mb-8 px-2 font-display text-xl font-black tracking-tighter text-grunge-acid">
        Salty Pickle
      </div>
      <nav className="flex flex-col gap-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-md px-3 py-2 text-sm font-semibold transition-all hover:bg-grunge-charcoal hover:text-grunge-acid hover:shadow-neon-acid ${
                isActive
                  ? 'bg-grunge-charcoal text-grunge-acid shadow-neon-acid'
                  : 'text-gray-300'
              }`
            }
          >
            <Icon className="h-4 w-4 shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
