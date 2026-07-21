import SubPageLayout from "@/components/landing/SubPageLayout";

export const metadata = { title: "Cookie Policy" };

export default function Page() {
  return (
    <SubPageLayout title="Cookie Policy" description="How HECTOR uses cookies and similar technologies.">
      <div className="space-y-6 text-silver text-sm">
        <p><strong className="text-white">Last updated:</strong> July 2026</p>
        <div>
          <h3 className="font-semibold text-white mb-2">1. What Are Cookies</h3>
          <p>Cookies are small text files stored on your device when you visit a website. They help the site remember your preferences and improve your experience.</p>
        </div>
        <div>
          <h3 className="font-semibold text-white mb-2">2. Cookies We Use</h3>
          <p>HECTOR uses essential cookies for authentication and session management. We do not use tracking cookies or third-party advertising cookies.</p>
        </div>
        <div>
          <h3 className="font-semibold text-white mb-2">3. Local Storage</h3>
          <p>HECTOR may use browser local storage to remember your language preferences and theme settings. This data stays on your device and is not transmitted to our servers.</p>
        </div>
        <div>
          <h3 className="font-semibold text-white mb-2">4. Managing Cookies</h3>
          <p>You can control cookies through your browser settings. Disabling essential cookies may affect the functionality of the service.</p>
        </div>
      </div>
    </SubPageLayout>
  );
}
