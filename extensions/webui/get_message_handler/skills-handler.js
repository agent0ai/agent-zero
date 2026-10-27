import { drawMessageToolSimple } from "/js/messages.js";

export default async function registerSkillsHandler(extData) {
  if (extData?.type === "skills_tool" || extData?.tool_name === "skills_tool") {
    extData.handler = (log) => {
      const displayKvps = { ...log.kvps };
      delete displayKvps._tool_name;
      return drawMessageToolSimple({ ...log, code: "SKL", displayKvps });
    };
  }
}
