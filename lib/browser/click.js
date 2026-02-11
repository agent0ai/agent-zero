// @ts-nocheck — plain JS, not a TypeScript file
// biome-ignore lint/correctness/noUnusedVariables: browser-injected function called via page.evaluate()
function click(selector) {
	{
		const element = document.querySelector(selector);
		if (element) {
			element.click();
			return true;
		}
		return false;
	}
}
