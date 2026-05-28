"""Flask server for streaming IK arm animation frames."""

from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO

from ikarms.animation import AnimationPreset, load_animation_presets
from ikarms.simulation import build_animation_frames, frame_to_payload
from ikarms.text_analysis import analyze_text


FRAME_DELAY_SECONDS = 0.016
ALLOWED_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)


def create_app() -> tuple[Flask, SocketIO]:
    """Create the Flask application and Socket.IO server."""
    app = Flask(__name__)

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": ALLOWED_ORIGINS,
            }
        },
    )

    socketio = SocketIO(
        app,
        cors_allowed_origins=ALLOWED_ORIGINS,
        async_mode="threading",
    )

    presets = _load_presets()
    preset_lookup = {preset.label.lower(): preset for preset in presets}

    @app.get("/api/health")
    def health() -> tuple[object, int]:
        """Return server health."""
        return jsonify({"status": "ok"}), 200

    @app.get("/api/animations")
    def animations() -> tuple[object, int]:
        """Return available animation labels."""
        return jsonify(
            {
                "animations": [
                    preset.label
                    for preset in presets
                ]
            }
        ), 200

    @app.post("/api/animations/<animation_name>/play")
    def play_animation(animation_name: str) -> tuple[object, int]:
        """Trigger animation playback by name."""
        preset = preset_lookup.get(animation_name.lower())

        if preset is None:
            return jsonify({"error": "Animation not found"}), 404

        _start_animation(socketio, preset)

        return jsonify(
            {
                "status": "started",
                "animation": preset.label,
            }
        ), 202

    @app.post("/api/chat/animate")
    def chat_animate() -> tuple[object, int]:
        """Analyze text, select an animation, and trigger it."""
        payload = request.get_json(silent=True) or {}
        text = str(payload.get("text", ""))

        analysis = analyze_text(text)
        preset = preset_lookup.get(analysis.animation.lower())

        if preset is None:
            return jsonify({"error": "Animation not found"}), 404

        _start_animation(socketio, preset)

        return jsonify(
            {
                "status": "started",
                "input": text,
                "analysis": analysis.to_dict(),
            }
        ), 202

    return app, socketio


def _start_animation(socketio: SocketIO, preset: AnimationPreset) -> None:
    """Start streaming one animation preset."""
    socketio.start_background_task(
        _stream_animation,
        socketio,
        preset,
    )


def _stream_animation(
    socketio: SocketIO,
    preset: AnimationPreset,
) -> None:
    """Stream interpolated animation frames through Socket.IO."""
    socketio.emit(
        "animation_started",
        {
            "label": preset.label,
        },
    )

    for frame in build_animation_frames(preset):
        socketio.emit(
            "arm_frame",
            frame_to_payload(frame),
        )
        socketio.sleep(FRAME_DELAY_SECONDS)

    socketio.emit(
        "animation_finished",
        {
            "label": preset.label,
        },
    )


def _load_presets() -> tuple[AnimationPreset, ...]:
    """Load animation presets from the project presets directory."""
    project_root = Path(__file__).resolve().parent.parent
    return load_animation_presets(project_root / "presets")


def main() -> None:
    """Run the Flask Socket.IO development server."""
    app, socketio = create_app()
    socketio.run(
        app,
        host="127.0.0.1",
        port=5000,
        debug=True,
        allow_unsafe_werkzeug=True,
    )


if __name__ == "__main__":
    main()