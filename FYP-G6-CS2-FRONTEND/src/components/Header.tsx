import type { Page } from "../types";

interface HeaderProps {
  page: Page;
  setPage: (page: Page) => void;
  role?: string;
  onReview: () => void;
  onLogout: () => Promise<void>;
  signedIn: boolean;
}

export function Header({
  page,
  setPage,
  role = "user",
  onReview,
  onLogout,
  signedIn,
}: HeaderProps) {
  return (
    <header>
      <a className="brand" onClick={() => setPage(signedIn ? "chat" : "welcome")}>
        <span className="mark">A</span> Alex
      </a>
      <span className="tag">A little space to breathe</span>
      {signedIn && (
        <nav>
          <button aria-current={page === "chat" ? "page" : undefined} onClick={() => setPage("chat")}>
            Chat
          </button>
          <button aria-current={page === "settings" ? "page" : undefined} onClick={() => setPage("settings")}>
            Settings
          </button>
          {(role === "admin" || role === "reviewer") && (
            <button onClick={onReview}>Review</button>
          )}
          <button onClick={onLogout}>Log out</button>
        </nav>
      )}
    </header>
  );
}
