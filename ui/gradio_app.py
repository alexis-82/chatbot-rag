"""UI Gradio: chat + pulsante re-index + lista file + indicatore provider."""
from __future__ import annotations

from typing import Callable

import gradio as gr


def _format_sources(sources: list[dict]) -> str:
    if not sources:
        return ""
    parts = []
    for s in sources:
        src = s.get("source", "?")
        page = s.get("page")
        parts.append(f"{src} p.{page}" if isinstance(page, int) else src)
    return "\n\n**Fonti:** " + ", ".join(parts)


def build_ui(
    chat_fn: Callable[[str], tuple[str, list[dict]]],
    reindex_fn: Callable[[], dict],
    list_files_fn: Callable[[], list[str]],
    provider_label: str,
) -> gr.Blocks:
    def _respond(message: str, history):
        reply, sources = chat_fn(message)
        return reply + _format_sources(sources)

    def _reindex():
        report = reindex_fn()
        files = list_files_fn()
        summary = (
            f"Re-indicizzazione completata — aggiunti: {report.get('added', 0)}, "
            f"aggiornati: {report.get('updated', 0)}, rimossi: {report.get('removed', 0)}."
        )
        return summary, "\n".join(f"- {f}" for f in files) or "(nessun file)"

    # Il blocco esterno del Chatbot ha overflow:auto e mostra una seconda
    # scrollbar mentre l'indicatore di "processing" sporge; i messaggi
    # scorrono comunque nel loro contenitore interno.
    css = "#chatbot { overflow: hidden !important; }"
    with gr.Blocks(title="Chatbot RAG locale", css=css) as demo:
        gr.Markdown(f"# Chatbot RAG locale\n**Provider attivo:** `{provider_label}`")
        with gr.Row(equal_height=True):
            with gr.Column(scale=4):
                chatbot = gr.Chatbot(
                    elem_id="chatbot",
                    type="messages",
                    height=650,
                    show_copy_button=True,
                    label="Chat",
                )
                gr.ChatInterface(fn=_respond, type="messages", chatbot=chatbot)
            with gr.Column(scale=1, min_width=260):
                gr.Markdown("### Documenti indicizzati")
                files_box = gr.Markdown(
                    "\n".join(f"- {f}" for f in list_files_fn()) or "(nessun file)"
                )
                reindex_btn = gr.Button("Re-indicizza documenti", variant="primary")
                reindex_status = gr.Markdown("")
                reindex_btn.click(fn=_reindex, outputs=[reindex_status, files_box])
    return demo
