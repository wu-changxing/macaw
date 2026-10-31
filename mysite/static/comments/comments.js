// Sign-to-comment: ask the wallet to sign the comment text, then POST it with the signature.
// The message format comes from the server (data-message) so both sides always build the same string.
(function () {
  const root = document.getElementById("wallet-comments");
  if (!root) return;
  const form = root.querySelector("[data-comment-form]");
  const status = root.querySelector("[data-status]");
  const list = root.querySelector("[data-comment-list]");

  const toHex = (text) =>
    "0x" + Array.from(new TextEncoder().encode(text), (b) => b.toString(16).padStart(2, "0")).join("");

  function render(comment) {
    root.querySelector("[data-empty]")?.remove();
    const li = document.createElement("li");
    li.className = "bg-white rounded p-4 shadow-sm";
    const meta = document.createElement("div");
    meta.className = "text-xs text-gray-500 mb-1";
    meta.textContent = comment.address + " · just now";
    const body = document.createElement("p");
    body.className = "text-gray-800 whitespace-pre-line";
    body.textContent = comment.body;
    li.append(meta, body);
    list.append(li);
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!window.ethereum) {
      status.textContent = "没有检测到钱包，请先安装 MetaMask。";
      return;
    }
    const body = form.body.value.trim();
    const button = form.querySelector("button");
    button.disabled = true;
    status.textContent = "请在钱包里确认签名…";

    const [address] = await window.ethereum.request({ method: "eth_requestAccounts" });
    const issuedAt = new Date().toISOString();
    const message = root.dataset.message
      .replace("{page_id}", () => root.dataset.pageId)
      .replace("{issued_at}", () => issuedAt)
      .replace("{body}", () => body);
    const signature = await window.ethereum
      .request({ method: "personal_sign", params: [toHex(message), address] })
      .catch(() => null);
    if (!signature) {
      status.textContent = "已取消签名。";
      button.disabled = false;
      return;
    }

    const response = await fetch(root.dataset.endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": form.csrfmiddlewaretoken.value },
      body: JSON.stringify({ page_id: root.dataset.pageId, body, issued_at: issuedAt, address, signature }),
    });
    const result = await response.json();
    button.disabled = false;
    if (!response.ok) {
      status.textContent = result.error;
      return;
    }
    render(result);
    form.reset();
    status.textContent = "已发布。";
  });
})();
