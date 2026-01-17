/** Async function that waits for specified number of time units. */
export async function sleep(miliseconds = 0, seconds = 0, minutes = 0, hours = 0, days = 0) {
  hours += days * 24;
  minutes += hours * 60;
  seconds += minutes * 60;
  miliseconds += seconds * 1000;
  
  // Maximum safe timeout is 1 hour (in milliseconds)
  const MAX_TIMEOUT = 60 * 60 * 1000;
  
  // if miliseconds is 0, wait at least one frame
  if (miliseconds === 0) {
    await new Promise((resolve) => setTimeout(resolve, 0));
    return;
  }

  // If the timeout is too large, break it into smaller chunks
  while (miliseconds > 0) {
    // Calculate the current chunk duration (1 hour max)
    const chunkDuration = Math.min(miliseconds, MAX_TIMEOUT);
    
    // Wait for the current chunk
    await new Promise((resolve) => setTimeout(resolve, chunkDuration));
    
    // Subtract the time we've waited
    miliseconds -= chunkDuration;
  }
}
export default sleep;

/** Equals to Sleep(0), but can be used to yield break a coroutine after N interations. */
let yieldIterations = 0;
export async function Yield(afterIterations = 1) {
  yieldIterations++;
  if (yieldIterations >= afterIterations) {
    await new Promise((resolve) => setTimeout(resolve, 0));
    yieldIterations = 0;
  }
}

/** Awaits equivalent of Sleep(0) N times which means it skips N-1 turns in the eventQueue.  */
export async function Skip(turns = 1) {
  while (turns > 0) {
    await new Promise((resolve) => setTimeout(resolve, 0));
    turns--;
  }
}