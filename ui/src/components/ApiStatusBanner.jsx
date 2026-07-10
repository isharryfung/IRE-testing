export default function ApiStatusBanner({ error }) {
  if (!error) {
    return null;
  }

  return (
    <div className="status-banner warning" role="status">
      <strong>Demo mode:</strong> {error}
    </div>
  );
}
