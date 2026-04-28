import { create } from "zustand";

export type TaskPhase =
  | "starting"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export interface TaskStatus {
  pubfileid: string;
  status: string;
  account: string;
  phase: TaskPhase;
  progress?: number | null;
  kind: "download" | "extract";
}

interface TasksState {
  tasks: Record<string, TaskStatus>;
  history: TaskStatus[];
  upsert: (task: TaskStatus) => void;
  complete: (pubfileid: string, kind: "download" | "extract") => void;
  clearFinished: () => void;
}

export const useTasksStore = create<TasksState>((set) => ({
  tasks: {},
  history: [],
  upsert: (task) =>
    set((state) => {
      const key = `${task.kind}:${task.pubfileid}`;
      const tasks = { ...state.tasks, [key]: task };
      if (["completed", "failed", "cancelled"].includes(task.phase)) {
        // Deduplicate: when the backend emits the same terminal phase
        // twice (download::status spam, manual cancel + auto-cancel from
        // the worker, etc.) we only want a single history row per task
        // run. We replace any previous entry with the same `kind+pubfileid`
        // so the history doesn't double up.
        const filtered = state.history.filter(
          (h) => !(h.kind === task.kind && h.pubfileid === task.pubfileid),
        );
        const history = [task, ...filtered].slice(0, 30);
        const next = { ...tasks };
        delete next[key];
        return { tasks: next, history };
      }
      return { tasks, history: state.history };
    }),
  complete: (pubfileid, kind) =>
    set((state) => {
      const next = { ...state.tasks };
      delete next[`${kind}:${pubfileid}`];
      return { tasks: next };
    }),
  clearFinished: () => set({ history: [] }),
}));
