'use client'

import { Scale, Activity, Bookmark, History } from 'lucide-react'
import { useAppStore } from '@/lib/store'
import styles from './Header.module.css'

export function Header() {
  const { activeTab, setActiveTab, searchHistory, bookmarks } = useAppStore()

  return (
    <header className={styles.header}>
      <div className={styles.logo}>
        <Scale className={styles.logoIcon} />
        <div className={styles.logoText}>
          <span className={styles.logoTitle}>HECTOR</span>
          <span className={styles.logoSubtitle}>Legal Intelligence</span>
        </div>
      </div>

      <nav className={styles.nav}>
        <button
          className={`${styles.navButton} ${activeTab === 'search' ? styles.active : ''}`}
          onClick={() => setActiveTab('search')}
        >
          <Activity size={18} />
          Research
        </button>
        <button
          className={`${styles.navButton} ${activeTab === 'compare' ? styles.active : ''}`}
          onClick={() => setActiveTab('compare')}
        >
          <Scale size={18} />
          Compare
        </button>
        <div className={styles.navDivider} />
        <button className={styles.navButton}>
          <History size={18} />
          <span className={styles.badge}>{searchHistory.length}</span>
        </button>
        <button className={styles.navButton}>
          <Bookmark size={18} />
          <span className={styles.badge}>{bookmarks.length}</span>
        </button>
      </nav>

      <div className={styles.statusIndicator}>
        <span className={styles.statusDot} />
        <span className={styles.statusText}>API Connected</span>
      </div>
    </header>
  )
}