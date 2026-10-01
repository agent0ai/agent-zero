# Sidebar Folders

Organize chats and tasks into project folders. Folder view is on by default; use **View** in the menu beside **New Chat** to choose **Folders** or **Flat mode**. View and sorting preferences are managed directly in that menu.

- Click a folder name to expand or collapse it. The selected chat's folder opens automatically.
- Use the **New chat** icon to create a chat in that project, regardless of the currently selected chat or project-inheritance setting.
- Folder actions include **New chat**, **Pin project**, **Edit project**, and **Project files**. Project pins use the bundled **Pin to Top** plugin.
- **No project** starts pinned at the top of the project folders. Its folder menu lets you unpin or pin it, remembers your choice, and includes **Projects** to open the global projects list.
- Pinned folders can be reordered among themselves, including **No project**. Unpinned folders stay below the pinned group; pin a folder first to move it into that group.
- Pinned chats appear together above all folders, including **No project**, separated by a divider. Project chats keep their colored dot and project context; chats without a project use the same pinning behavior. Unpinning returns a chat to its folder. Parallel workers stay nested with their parent.
- Drag folders or chats between rows to reorder them. Reordering folders, chats, or tasks automatically selects **Manual order**. Reorder pins within their section without changing their projects; use the row menu to pin or unpin.
- Drop a chat onto a project folder to switch its project context, or onto **No project** to remove its project assignment. Its parallel children stay with it. Stop a running chat and its parallel calls before moving them. Existing transcript and files are retained; this changes the project used for subsequent work, without relocating files.
- Scheduler tasks have their own pinned section and project folders. Their configured project stays unchanged when reordered.
- Chats and tasks default to **Created time**, newest first, so new messages do not change their position. **Last active**, name, and manual order are also available. Filter by project, **Working** / **Idle** status, or recent activity. Idle includes waiting or completed chats, paused chats, and disabled tasks. A working parallel child keeps its family under Working.

View and sort settings, project pins, and manual order are saved for the instance. Folder expansion is saved in the browser; filters apply to the current page. Disabling this plugin restores the standard sidebar.
