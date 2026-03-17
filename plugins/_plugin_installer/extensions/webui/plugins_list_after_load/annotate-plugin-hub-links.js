import { store as pluginInstallStore } from "../../../webui/pluginInstallStore.js";

function getPluginName(plugin) {
  return typeof plugin?.name === "string" ? plugin.name.trim() : "";
}

function getPluginHubMatch(plugin, pluginHubPlugins) {
  const pluginName = getPluginName(plugin);
  if (!pluginName || !pluginHubPlugins?.[pluginName]) {
    return null;
  }

  return {
    key: pluginName,
    title: pluginHubPlugins[pluginName]?.title || pluginName,
  };
}

export default async function annotatePluginHubLinks(context) {
  const plugins = Array.isArray(context?.plugins) ? context.plugins : null;
  const store = context?.store;
  if (!plugins?.length) return;

  const loaded = await pluginInstallStore.ensureIndexLoaded({ background: true });
  if (!loaded) return;

  const pluginHubPlugins = pluginInstallStore.index?.plugins;
  if (!pluginHubPlugins || typeof pluginHubPlugins !== "object") return;

  let changed = false;
  for (const plugin of plugins) {
    if (!plugin || typeof plugin !== "object") continue;

    const nextPluginHub = getPluginHubMatch(plugin, pluginHubPlugins);
    const currentKey = plugin?.pluginHub?.key || "";
    const nextKey = nextPluginHub?.key || "";
    if (currentKey === nextKey) continue;

    plugin.pluginHub = nextPluginHub;
    changed = true;
  }

  if (changed && store?.plugins === plugins) {
    store.plugins = [...plugins];
  }
}
