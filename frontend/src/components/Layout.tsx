import { type ReactNode } from 'react'
import pileupBusterLogo from '../assets/logo.png'
import pileupBusterLogoDark from '../assets/logo-dark.png'
import ThemeToggle from '../components/ThemeToggle'
import { useTheme } from '../contexts/ThemeContext'

interface LayoutProps {
  children: ReactNode
  headerControls?: ReactNode
}

export default function Layout({ children, headerControls }: LayoutProps) {
  const { resolvedTheme } = useTheme()

  return (
    <div className="pileup-buster-app">
      {/* Header */}
      <header className="header">
        <img 
          src={resolvedTheme === 'dark' ? pileupBusterLogoDark : pileupBusterLogo} 
          alt="Pileup Buster Logo" 
          className="logo"
        />
        <div className="header-controls">
          <ThemeToggle />
          {headerControls}
        </div>
      </header>

      {children}

      {/* Footer */}
      <footer className="footer">
        <div className="footer-content">
          <a 
            href="https://ei6jgb.com" 
            target="_blank" 
            rel="noopener noreferrer"
            className="github-link"
          >
          Maintained by EI6JGB. Original by BrianBruff (Ei6LF)
          </a>
        </div>
      </footer>
    </div>
  )
}
