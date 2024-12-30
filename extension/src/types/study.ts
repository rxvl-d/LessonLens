interface StudyTask {
    search_task: string;
    feature_flags: string[];
    relevance_dimensions: string[];
}

interface StudySettings {
    subject: string;
    tasks: StudyTask[];
}

export {StudyTask, StudySettings}