"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { io, Socket } from "socket.io-client";

const SERVER_URL = "http://127.0.0.1:5000";
const CANVAS_WIDTH = 900;
const CANVAS_HEIGHT = 600;

type NormalizedPoint = {
  x: number;
  y: number;
};

type FingerSegment = {
  start: NormalizedPoint;
  end: NormalizedPoint;
};

type ArmFrame = {
  controls: {
    target_x: number;
    target_y: number;
    pivot_angle: number;
    claw_value: number;
  };
  points: {
    shoulder: NormalizedPoint;
    elbow: NormalizedPoint;
    wrist: NormalizedPoint;
    wrist_tip: NormalizedPoint;
    target: NormalizedPoint;
    fingers: FingerSegment[];
  };
};

type ChatAnalysis = {
  animation: string;
  confidence: number;
  reason: string;
};

function remapPoint(point: NormalizedPoint): [number, number] {
  return [point.x * CANVAS_WIDTH, point.y * CANVAS_HEIGHT];
}

function drawSegment(
  context: CanvasRenderingContext2D,
  start: NormalizedPoint,
  end: NormalizedPoint,
  color: string,
  width: number,
): void {
  const [startX, startY] = remapPoint(start);
  const [endX, endY] = remapPoint(end);

  context.strokeStyle = color;
  context.lineWidth = width;
  context.lineCap = "round";

  context.beginPath();
  context.moveTo(startX, startY);
  context.lineTo(endX, endY);
  context.stroke();
}

function drawJoint(
  context: CanvasRenderingContext2D,
  point: NormalizedPoint,
): void {
  const [xPosition, yPosition] = remapPoint(point);

  context.fillStyle = "rgb(255, 255, 255)";
  context.strokeStyle = "rgb(8, 12, 20)";
  context.lineWidth = 2;

  context.beginPath();
  context.arc(xPosition, yPosition, 8, 0, Math.PI * 2);
  context.fill();
  context.stroke();
}

function drawTarget(
  context: CanvasRenderingContext2D,
  target: NormalizedPoint,
): void {
  const [xPosition, yPosition] = remapPoint(target);
  const size = 8;

  context.strokeStyle = "rgb(255, 0, 255)";
  context.lineWidth = 2;

  context.beginPath();
  context.moveTo(xPosition - size, yPosition);
  context.lineTo(xPosition + size, yPosition);
  context.moveTo(xPosition, yPosition - size);
  context.lineTo(xPosition, yPosition + size);
  context.stroke();
}

function drawArmFrame(
  context: CanvasRenderingContext2D,
  frame: ArmFrame,
): void {
  context.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

  const gradient = context.createRadialGradient(
    CANVAS_WIDTH * 0.45,
    CANVAS_HEIGHT * 0.4,
    80,
    CANVAS_WIDTH * 0.5,
    CANVAS_HEIGHT * 0.5,
    CANVAS_WIDTH,
  );

  gradient.addColorStop(0, "rgba(30, 41, 59, 0.72)");
  gradient.addColorStop(1, "rgba(8, 12, 20, 0)");

  context.fillStyle = gradient;
  context.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

  drawTarget(context, frame.points.target);

  drawSegment(
    context,
    frame.points.shoulder,
    frame.points.elbow,
    "rgb(255, 0, 0)",
    10,
  );
  drawSegment(
    context,
    frame.points.elbow,
    frame.points.wrist,
    "rgb(0, 255, 0)",
    10,
  );
  drawSegment(
    context,
    frame.points.wrist,
    frame.points.wrist_tip,
    "rgb(0, 0, 255)",
    8,
  );

  frame.points.fingers.forEach((finger) => {
    drawSegment(
      context,
      finger.start,
      finger.end,
      "rgb(255, 255, 0)",
      5,
    );
  });

  drawJoint(context, frame.points.shoulder);
  drawJoint(context, frame.points.elbow);
  drawJoint(context, frame.points.wrist);
}

async function fetchAnimations(): Promise<string[]> {
  const response = await fetch(`${SERVER_URL}/api/animations`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to fetch animations.");
  }

  const payload = (await response.json()) as { animations: string[] };
  return payload.animations;
}

async function playAnimation(animationName: string): Promise<void> {
  const response = await fetch(
    `${SERVER_URL}/api/animations/${animationName}/play`,
    {
      method: "POST",
    },
  );

  if (!response.ok) {
    throw new Error(`Failed to play animation: ${animationName}`);
  }
}

async function sendChatMessage(text: string): Promise<ChatAnalysis> {
  const response = await fetch(`${SERVER_URL}/api/chat/animate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    throw new Error("Failed to analyze chat message.");
  }

  const payload = (await response.json()) as {
    analysis: ChatAnalysis;
  };

  return payload.analysis;
}

export default function Home() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const socketRef = useRef<Socket | null>(null);

  const [animations, setAnimations] = useState<string[]>([]);
  const [activeAnimation, setActiveAnimation] = useState<string>("Idle");
  const [connectionStatus, setConnectionStatus] = useState<string>("Offline");
  const [chatText, setChatText] = useState<string>("");
  const [latestAnalysis, setLatestAnalysis] = useState<ChatAnalysis | null>(
    null,
  );

  useEffect(() => {
    fetchAnimations()
      .then(setAnimations)
      .catch((error: unknown) => {
        console.error(error);
        setAnimations([]);
      });
  }, []);

  useEffect(() => {
    const socket = io(SERVER_URL, {
      transports: ["websocket"],
    });

    socketRef.current = socket;

    socket.on("connect", () => {
      setConnectionStatus("Online");
    });

    socket.on("disconnect", () => {
      setConnectionStatus("Offline");
    });

    socket.on("animation_started", (payload: { label: string }) => {
      setActiveAnimation(payload.label);
    });

    socket.on("animation_finished", () => {
      setActiveAnimation("Idle");
    });

    socket.on("arm_frame", (frame: ArmFrame) => {
      const canvas = canvasRef.current;
      const context = canvas?.getContext("2d");

      if (context) {
        drawArmFrame(context, frame);
      }
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  async function handleChatSubmit(event: FormEvent): Promise<void> {
    event.preventDefault();

    const trimmedText = chatText.trim();

    if (!trimmedText) {
      return;
    }

    try {
      const analysis = await sendChatMessage(trimmedText);
      setLatestAnalysis(analysis);
      setChatText("");
    } catch (error) {
      console.error(error);
    }
  }

  return (
    <main className="relative flex min-h-screen overflow-hidden text-slate-100">
      <div className="pointer-events-none fixed left-6 top-6 z-20 flex items-center gap-3">
        <span className="rounded-full bg-white/10 px-4 py-2 text-sm text-slate-200 backdrop-blur-xl">
          {connectionStatus}
        </span>

        <span className="rounded-full bg-cyan-300/10 px-4 py-2 text-sm text-cyan-100 backdrop-blur-xl">
          {activeAnimation}
        </span>

        {latestAnalysis && (
          <span className="hidden rounded-full bg-white/10 px-4 py-2 text-sm text-slate-300 backdrop-blur-xl md:inline">
            {latestAnalysis.animation}
          </span>
        )}
      </div>

      <div className="fixed right-6 top-6 z-20 flex flex-wrap justify-end gap-2">
        {animations.map((animationName) => (
          <button
            key={animationName}
            onClick={() => {
              void playAnimation(animationName);
            }}
            className="rounded-full bg-white/10 px-4 py-2 text-sm font-medium text-slate-100 shadow-lg shadow-black/20 backdrop-blur-xl transition hover:bg-cyan-300/20 hover:text-cyan-100 active:scale-95"
            type="button"
          >
            {animationName}
          </button>
        ))}
      </div>

      <section className="flex min-h-screen w-full items-center justify-center px-4 pb-32 pt-20">
        <canvas
          ref={canvasRef}
          width={CANVAS_WIDTH}
          height={CANVAS_HEIGHT}
          className="block h-auto w-full max-w-5xl bg-transparent"
        />
      </section>

      <form
        onSubmit={(event) => {
          void handleChatSubmit(event);
        }}
        className="fixed bottom-6 left-1/2 z-30 flex w-[min(920px,calc(100vw-32px))] -translate-x-1/2 items-center gap-3 rounded-full bg-white/10 p-2 shadow-2xl shadow-black/30 backdrop-blur-2xl ring-1 ring-white/10"
      >
        <input
          value={chatText}
          onChange={(event) => setChatText(event.target.value)}
          placeholder="Type a message..."
          className="min-w-0 flex-1 rounded-full bg-transparent px-5 py-4 text-base text-slate-100 outline-none placeholder:text-slate-400"
        />

        <button
          type="submit"
          className="rounded-full bg-cyan-300 px-6 py-4 text-sm font-semibold text-slate-950 shadow-lg shadow-cyan-950/30 transition hover:bg-cyan-200 active:scale-95"
        >
          Send
        </button>
      </form>
    </main>
  );
}