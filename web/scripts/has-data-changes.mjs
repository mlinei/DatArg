import { repositoryChanges } from './data-changes.mjs';

process.exit((await repositoryChanges()).length ? 0 : 1);
