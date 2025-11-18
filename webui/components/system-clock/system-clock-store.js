import { createStore } from "/js/AlpineStore.js";

const model = {
  currentTime: "",
  displayTime: "",
  displayDate: "",

  init() {
    // no-op for now
  },

  updateFromPoll(pollData) {
    if (!pollData) return;

    const systemTime = pollData.system_time;
    if (!systemTime || systemTime === this.currentTime) {
      return;
    }

    this.currentTime = systemTime;

    const isoMatch = systemTime.match(
      /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2}))?(?:Z|[+-]\d{2}:\d{2})?$/
    );

    if (isoMatch) {
      const [, year, month, day, hour, minute, second] = isoMatch;

      const displayDate = new Date(
        Date.UTC(
          parseInt(year, 10),
          parseInt(month, 10) - 1,
          parseInt(day, 10),
          parseInt(hour, 10),
          parseInt(minute, 10),
          second ? parseInt(second, 10) : 0
        )
      );

      const timeFormatter = new Intl.DateTimeFormat(undefined, {
        hour: "numeric",
        minute: "2-digit",
        timeZone: "UTC",
      });

      const dateFormatter = new Intl.DateTimeFormat(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
        timeZone: "UTC",
      });

      this.displayTime = timeFormatter.format(displayDate);
      this.displayDate = dateFormatter.format(displayDate);
      return;
    }

    this.displayTime = systemTime;
    this.displayDate = "";
  },
};

const store = createStore("systemClockStore", model);

export { store };