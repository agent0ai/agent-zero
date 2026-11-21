export const slides = [
  {
    id: "a0-cleaner",
    eyebrow: "New built-in plugin",
    title: "Free up space with AOCleaner",
    summary: "Clear old caches, screenshots, and leftovers that build up as you use Agent Zero.",
    mediaType: "image",
    media: "/plugins/_whats_new/webui/assets/a0-cleaner.png",
    mediaLabel: "A0Cleaner showing disk usage, automatic cleanup, and a notification with files for review.",
    bullets: [
      {
        title: "Automatic cleanup",
        text: "is on by default and runs on Monday at 9 AM. Choose what it cleans and adjust the schedule in the config page.",
      },
      {
        title: "Review files",
        text: "before a manual cleanup. You can add custom folders.",
      },
      {
        title: "Find it",
        text: "in Plugins → Builtin → AOCleaner → Open for the plugin screen.",
      },
    ],
  },
  {
    id: "scheduler-catchup",
    eyebrow: "Improved scheduled tasks",
    title: "Your scheduled tasks catch up after downtime",
    summary: "If Agent Zero is offline when a recurring task is due, it runs automatically when your instance is back online.",
    mediaType: "image",
    media: "/plugins/_whats_new/webui/assets/scheduler-catchup.png",
    mediaLabel: "Scheduled Tasks showing task schedules, status, and actions.",
    bullets: [
      {
        title: "Back on schedule",
        text: "Several missed runs become one catch-up run, then the usual schedule continues.",
      },
      {
        title: "You're in control",
        text: "Disabled tasks stay off. Tasks interrupted while running need your attention in Scheduled Tasks.",
      },
    ],
  },
];
