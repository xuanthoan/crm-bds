type FormErrorProps = {
  messages: string[] | null;
};

export function FormError({ messages }: FormErrorProps) {
  if (!messages || messages.length === 0) {
    return null;
  }

  return (
    <div className="form-error">
      {messages.length === 1 ? (
        messages[0]
      ) : (
        <ul>
          {messages.map((message) => (
            <li key={message}>{message}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
