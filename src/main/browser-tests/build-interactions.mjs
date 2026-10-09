import {build} from 'vite';
import {fileURLToPath} from 'node:url';
await build({configFile:false, root:fileURLToPath(new URL('.',import.meta.url)), base:'/test/', build:{outDir:fileURLToPath(new URL('../../../.tmp/interaction-dist',import.meta.url)),emptyOutDir:true,rollupOptions:{input:['interactions.html', 'panes.html', 'operational.html'].map(name => fileURLToPath(new URL(name,import.meta.url)))}}});
