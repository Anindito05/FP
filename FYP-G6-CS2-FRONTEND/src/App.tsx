import { AdminPage } from "./components/AdminPage";
import { AuthPage } from "./components/AuthPage";
import { ChatPage } from "./components/ChatPage";
import { Header } from "./components/Header";
import { SettingsPage } from "./components/SettingsPage";
import { WelcomePage } from "./components/WelcomePage";
import { useAppController } from "./hooks/useAppController";

export function App() {
  const app = useAppController();

  return (
    <div className="app">
      <Header
        page={app.page}
        setPage={app.setPage}
        role={app.user?.role}
        signedIn={Boolean(app.access)}
        onReview={app.openAdmin}
        onLogout={app.logout}
      />

      {app.page === "welcome" && (
        <WelcomePage
          accepted={app.terms}
          onAcceptedChange={app.setTerms}
          onContinue={app.acceptDisclaimer}
        />
      )}

      {app.page === "auth" && (
        <AuthPage
          name={app.name}
          email={app.email}
          password={app.password}
          error={app.error}
          acceptedTerms={app.authTerms}
          busy={app.authBusy}
          onNameChange={app.setName}
          onEmailChange={app.setEmail}
          onPasswordChange={app.setPassword}
          onAcceptedTermsChange={app.setAuthTerms}
          onClearError={() => app.setError("")}
          onAuthenticate={app.authenticate}
        />
      )}

      {app.page === "chat" && (
        <ChatPage
          sessions={app.sessions}
          sessionId={app.sessionId}
          messages={app.messages}
          draft={app.draft}
          busy={app.busy}
          creatingSession={app.creatingSession}
          dataConsent={app.dataConsent}
          error={app.error}
          city={app.city}
          country={app.country}
          locationConsent={app.locationConsent}
          resources={app.resources}
          onCreateSession={app.createSession}
          onDataConsent={(granted) => void app.updateConsent("data_logging", granted)}
          onSelectSession={app.selectSession}
          onCloseSession={app.closeSession}
          onDraftChange={app.setDraft}
          onSend={app.sendMessage}
          onCityChange={app.setCity}
          onCountryChange={app.setCountry}
          onLocationConsent={(granted) =>
            void app.updateConsent("location_lookup", granted)
          }
          onOfferChoice={app.respondToOffer}
          onFeedback={app.submitFeedback}
          onDismissError={() => app.setError("")}
        />
      )}

      {app.page === "settings" && (
        <SettingsPage
          onConsentChange={app.updateConsent}
        consents={{ data_logging: app.dataConsent, location_lookup: app.locationConsent, research_use: app.researchConsent }}
          onBack={() => app.setPage("chat")}
          onDeleteAccount={app.deleteAccount}
        />
      )}

      {app.page === "admin" && (
        <AdminPage
          data={app.adminData}
          onReview={app.reviewRiskEvent}
          onBack={() => app.setPage("chat")}
        />
      )}

      {app.error && app.page !== "auth" && app.page !== "chat" && (
        <div className="errorbar">
          {app.error}
          <button onClick={() => app.setError("")}>Dismiss</button>
        </div>
      )}
      <footer>If you are in immediate danger, contact your local emergency number.</footer>
    </div>
  );
}
