TASK_ROUTES = {
    "scraper_worker.tasks.*": {"queue": "scraping"},
    "ai_worker.tasks.*": {"queue": "ai"},
}
