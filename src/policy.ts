const blocked=[/rm\s+-rf\s+\//i,/mkfs\b/i,/dd\s+if=/i,/shutdown\b/i,/reboot\b/i,/curl[^\n]*\|\s*(sh|bash)/i,/wget[^\n]*\|\s*(sh|bash)/i,/sudo\b/i,/chmod\s+777/i,/npm\s+install\s+-g/i,/cat\s+.*\.env/i,/cat\s+.*id_rsa/i,/printenv\b/i];
export function assertSafeShell(command:string){if(command.length>2000)throw new Error('Command too long.');if(blocked.some(r=>r.test(command)))throw new Error('Blocked by safety policy.')}
export function assertSafePath(filePath:string){if(filePath.includes('..')||filePath.startsWith('/')||/(^|[/\\])\.env($|\.)/i.test(filePath))throw new Error('Unsafe path.')}
