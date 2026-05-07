import { Search } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'

export default function Header({ onSearchOpen }) {
  const { user } = useAuth()

  return (
    <header className="fixed left-60 right-0 top-0 z-30 flex h-14 items-center justify-between border-b border-border bg-card px-4">
      <Button
        variant="outline"
        className="relative h-8 w-full justify-start rounded-md bg-background text-sm font-normal text-muted-foreground shadow-none sm:pr-12 md:w-40 lg:w-64"
        onClick={onSearchOpen}
      >
        <Search className="mr-2 h-4 w-4" />
        검색...
        <kbd className="pointer-events-none absolute right-1.5 top-1.5 hidden h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium opacity-100 sm:flex">
          <span className="text-xs">⌘</span>K
        </kbd>
      </Button>

      <div className="flex items-center gap-3">
        {user && (
          <div className="flex items-center gap-2 text-sm">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold">
              {user.name?.charAt(0) || '?'}
            </div>
            <span className="hidden font-medium sm:inline">{user.name}</span>
            <span className="hidden text-muted-foreground md:inline">({user.username})</span>
          </div>
        )}
      </div>
    </header>
  )
}
