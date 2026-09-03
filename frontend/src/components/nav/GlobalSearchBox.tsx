import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { listIssues } from "@/api/issues";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";

export function GlobalSearchBox() {
  const navigate = useNavigate();
  const containerRef = useRef<HTMLDivElement>(null);
  const [term, setTerm] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const debouncedTerm = useDebouncedValue(term, 250);

  const { data: results } = useQuery({
    queryKey: ["global-search", debouncedTerm],
    queryFn: () => listIssues({ q: debouncedTerm, limit: 10 }),
    enabled: debouncedTerm.trim().length > 0,
  });

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function goToIssue(key: string) {
    setIsOpen(false);
    setTerm("");
    navigate(`/issues/${key}`);
  }

  function goToSearchPage() {
    setIsOpen(false);
    navigate(`/issues?q=${encodeURIComponent(term)}`);
  }

  const showDropdown = isOpen && term.trim().length > 0;

  return (
    <div ref={containerRef} className="relative w-full max-w-md">
      <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
      <Input
        placeholder="Search all issues…"
        value={term}
        onChange={(e) => {
          setTerm(e.target.value);
          setIsOpen(true);
        }}
        onFocus={() => setIsOpen(true)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && term.trim()) goToSearchPage();
          if (e.key === "Escape") setIsOpen(false);
        }}
        className="pl-8"
      />
      {showDropdown && (
        <div className="absolute top-full left-0 z-50 mt-1 w-full rounded-md border bg-popover text-popover-foreground shadow-md">
          {!results?.length ? (
            <div className="px-3 py-2 text-sm text-muted-foreground">No matching issues</div>
          ) : (
            <ul className="max-h-80 overflow-y-auto py-1">
              {results.map((issue) => (
                <li key={issue.id}>
                  <button
                    type="button"
                    onClick={() => goToIssue(issue.key)}
                    className="flex w-full items-center gap-2 px-3 py-1.5 text-left text-sm hover:bg-accent hover:text-accent-foreground"
                  >
                    <span className="font-mono text-xs text-muted-foreground">{issue.key}</span>
                    <span className="truncate">{issue.summary}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
