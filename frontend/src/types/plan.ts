export interface PlanTask {
  description: string;
  status: string;
}

export interface Plan {
  tasks: PlanTask[];
  format: string;
}
