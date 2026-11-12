import { useEffect, useState } from 'react'
import { NavLink, Route, Routes } from 'react-router-dom'
import { Activity, Beaker, History, Info, KeyRound, LayoutDashboard, Menu, Moon, Plus, Sun, X } from 'lucide-react'
import { DashboardPage } from './pages/DashboardPage'
import { NewEvaluationPage } from './pages/NewEvaluationPage'
import { RunPage } from './pages/RunPage'
import { HistoryPage } from './pages/HistoryPage'
import { ArchitecturePage } from './pages/ArchitecturePage'
import { WorkspaceAccess } from './components/WorkspaceAccess'

const nav = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/new', label: 'New evaluation', icon: Plus },
  { to: '/history', label: 'History', icon: History },
  { to: '/architecture', label: 'How it works', icon: Activity },
]

export default function App() {
  const [dark, setDark] = useState(() => localStorage.getItem('aql-theme') !== 'light')
  const [menu, setMenu] = useState(false)
  const [workspaceAccess, setWorkspaceAccess] = useState(false)
  useEffect(() => {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light'
    localStorage.setItem('aql-theme', dark ? 'dark' : 'light')
  }, [dark])
  return (
    <div className="app-shell">
      <aside className={`sidebar ${menu ? 'sidebar-open' : ''}`}>
        <div className="brand"><span className="brand-mark"><Beaker size={21} /></span><div><b>AI Quality Lab</b><small>Explainable evaluation</small></div></div>
        <button className="icon-btn mobile-close" onClick={() => setMenu(false)} aria-label="Close navigation"><X /></button>
        <nav>{nav.map(({ to, label, icon: Icon, end }) => <NavLink key={to} to={to} end={end} onClick={() => setMenu(false)}><Icon size={18} />{label}</NavLink>)}</nav>
        <div className="sidebar-bottom"><button className="workspace-button" onClick={() => { setWorkspaceAccess(true); setMenu(false) }}><KeyRound size={16} /><span><b>Workspace access</b><small>Connect another device</small></span></button><div className="sidebar-note"><Info size={16} /><span>Scores distinguish deterministic checks, heuristics, and optional model judgment.</span></div></div>
      </aside>
      {menu && <button className="menu-backdrop" aria-label="Close menu" onClick={() => setMenu(false)} />}
      <main className="main">
        <header className="topbar">
          <button className="icon-btn menu-trigger" onClick={() => setMenu(true)} aria-label="Open navigation"><Menu /></button>
          <div className="topbar-title"><Beaker size={18} /><span>AI Quality Lab</span></div>
          <button className="icon-btn" onClick={() => setDark(v => !v)} aria-label={`Use ${dark ? 'light' : 'dark'} theme`}>{dark ? <Sun /> : <Moon />}</button>
        </header>
        <div className="page-wrap">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/new" element={<NewEvaluationPage />} />
            <Route path="/runs/:id" element={<RunPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/architecture" element={<ArchitecturePage />} />
            <Route path="*" element={<DashboardPage />} />
          </Routes>
        </div>
      </main>
      {workspaceAccess && <WorkspaceAccess onClose={() => setWorkspaceAccess(false)} />}
    </div>
  )
}
