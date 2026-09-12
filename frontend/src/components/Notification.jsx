export default function Notification({ notice }) {
  if (!notice) return null;

  return (
    <div className={`agent-notification active ${notice.type ?? "info"}`}>
      <strong>{notice.title}</strong>
      <span>{notice.message}</span>
    </div>
  );
}
