import { useState } from 'react'
import Sidebar from './Sidebar'
import Header from './Header'
import SearchCommand from './SearchCommand'

export default function Layout({ children }) {
  const [searchOpen, setSearchOpen] = useState(false)

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <Header onSearchOpen={() => setSearchOpen(true)} />
      <main className="ml-60 mt-14 min-h-[calc(100vh-3.5rem)] p-6">
        <div className="max-w-6xl mx-auto">
          {children}
        </div>
      </main>
      <SearchCommand open={searchOpen} onOpenChange={setSearchOpen} />
    </div>
  )
}
