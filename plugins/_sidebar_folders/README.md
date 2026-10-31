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
- **Search** is the last option in the same menu: **Standard** puts the search field below Chats, **Compact** opens it from the magnifier beside New Chat, and **No search** removes it and clears the query. Standard is the default.
- Search chat/task names and loaded message text together. Existing filters still apply. Matching excerpts open the relevant conversation, including matching child chats. Matching folders open temporarily; clearing restores their saved state. Use the close button or Escape to clear. Sidebar and Welcome Chats searches are independent.
- Message previews emphasize matching words beneath the thread title. Title-only matches do not repeat the title; a matching child title remains clickable beneath its parent.

View, sort, Project, Status, Last activity, and Search choices save automatically for the instance and survive reloads, along with project pins and manual order. Search text is temporary and covers loaded conversations, not deleted or archived chats. Folder expansion is saved in the browser. Disabling this plugin restores the standard sidebar.
