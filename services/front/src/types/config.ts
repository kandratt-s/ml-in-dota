export type ModelKind = "boosting" | "logreg";
export type TimeWindow = 1 | 5 | 10 | 15 | 20;
export type Interval = 1 | 3 | 5;

export interface SessionConfig {
  model: ModelKind;
  time: TimeWindow;
  interval: Interval;
  full_map: boolean;
}

export const DEFAULT_CONFIG: SessionConfig = {
  model: "boosting",
  time: 10,
  interval: 1,
  full_map: true,
};

export const MODEL_OPTIONS: ModelKind[] = ["boosting", "logreg"];
export const TIME_OPTIONS: TimeWindow[] = [1, 5, 10, 15, 20];
export const INTERVAL_OPTIONS: Interval[] = [1, 3, 5];

export interface PredictionFrame {
  token: string;
  timestamp: string;
  radiant_win_prob: number;
  source: string;
}
