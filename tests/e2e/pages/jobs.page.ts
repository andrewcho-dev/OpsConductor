import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './base.page';

export class JobsPage extends BasePage {
  readonly pageTitle: Locator;
  readonly createJobButton: Locator;
  readonly jobsTable: Locator;
  readonly searchField: Locator;
  readonly filterButtons: Locator;
  readonly refreshButton: Locator;
  readonly bulkActionsButton: Locator;
  
  // Job creation modal
  readonly createJobModal: Locator;
  readonly jobNameField: Locator;
  readonly jobDescriptionField: Locator;
  readonly jobTypeSelect: Locator;
  readonly actionSelect: Locator;
  readonly targetSelectionButton: Locator;
  readonly scheduleJobButton: Locator;
  readonly saveJobButton: Locator;
  readonly cancelJobButton: Locator;
  
  // Job execution controls
  readonly executeJobButton: Locator;
  readonly stopJobButton: Locator;
  readonly viewJobHistoryButton: Locator;
  readonly viewJobResultsButton: Locator;
  
  // Job history and results
  readonly jobHistoryModal: Locator;
  readonly jobResultsModal: Locator;
  readonly executionLogs: Locator;
  readonly executionStatus: Locator;
  
  // Scheduling modal
  readonly scheduleModal: Locator;
  readonly scheduleTypeSelect: Locator;
  readonly cronExpressionField: Locator;
  readonly intervalField: Locator;
  readonly startTimeField: Locator;
  readonly endTimeField: Locator;
  readonly saveScheduleButton: Locator;
  
  // Actions workspace
  readonly actionsWorkspaceButton: Locator;
  readonly actionsWorkspaceModal: Locator;
  readonly actionsList: Locator;
  readonly addActionButton: Locator;
  readonly removeActionButton: Locator;
  readonly actionConfigFields: Locator;

  constructor(page: Page) {
    super(page);
    this.pageTitle = page.locator('h1:has-text("Jobs"), h2:has-text("Jobs")').first();
    this.createJobButton = page.locator('button:has-text("Create Job"), button:has-text("New Job"), button:has-text("Add Job")').first();
    this.jobsTable = page.locator('table, [role="grid"], .data-grid').first();
    this.searchField = page.locator('input[placeholder*="search" i], input[type="search"]').first();
    this.filterButtons = page.locator('button:has-text("Filter"), .filter-button');
    this.refreshButton = page.locator('button[aria-label*="refresh" i], button:has-text("Refresh")').first();
    this.bulkActionsButton = page.locator('button:has-text("Bulk Actions")').first();
    
    // Job creation
    this.createJobModal = page.locator('[role="dialog"]:has-text("Create Job"), [role="dialog"]:has-text("New Job")').first();
    this.jobNameField = page.locator('input[name="name"], input[placeholder*="name" i]').first();
    this.jobDescriptionField = page.locator('textarea[name="description"], input[name="description"]').first();
    this.jobTypeSelect = page.locator('select[name="type"], [role="combobox"]').first();
    this.actionSelect = page.locator('select[name="action"], [role="combobox"]:has-text("Action")').first();
    this.targetSelectionButton = page.locator('button:has-text("Select Targets")').first();
    this.scheduleJobButton = page.locator('button:has-text("Schedule")').first();
    this.saveJobButton = page.locator('button:has-text("Save"), button:has-text("Create"), button[type="submit"]').first();
    this.cancelJobButton = page.locator('button:has-text("Cancel")').first();
    
    // Execution controls
    this.executeJobButton = page.locator('button:has-text("Execute"), button:has-text("Run")').first();
    this.stopJobButton = page.locator('button:has-text("Stop"), button:has-text("Cancel")').first();
    this.viewJobHistoryButton = page.locator('button:has-text("History")').first();
    this.viewJobResultsButton = page.locator('button:has-text("Results"), button:has-text("View Results")').first();
    
    // History and results
    this.jobHistoryModal = page.locator('[role="dialog"]:has-text("History"), [role="dialog"]:has-text("Execution History")').first();
    this.jobResultsModal = page.locator('[role="dialog"]:has-text("Results")').first();
    this.executionLogs = page.locator('.execution-logs, .job-logs, pre').first();
    this.executionStatus = page.locator('.status, .execution-status').first();
    
    // Scheduling
    this.scheduleModal = page.locator('[role="dialog"]:has-text("Schedule")').first();
    this.scheduleTypeSelect = page.locator('select[name="scheduleType"]').first();
    this.cronExpressionField = page.locator('input[name="cron"], input[placeholder*="cron" i]').first();
    this.intervalField = page.locator('input[name="interval"]').first();
    this.startTimeField = page.locator('input[name="startTime"], input[type="datetime-local"]').first();
    this.endTimeField = page.locator('input[name="endTime"]').first();
    this.saveScheduleButton = page.locator('button:has-text("Save Schedule")').first();
    
    // Actions workspace
    this.actionsWorkspaceButton = page.locator('button:has-text("Actions Workspace")').first();
    this.actionsWorkspaceModal = page.locator('[role="dialog"]:has-text("Actions Workspace")').first();
    this.actionsList = page.locator('.actions-list, .action-items').first();
    this.addActionButton = page.locator('button:has-text("Add Action"), button:has-text("+")').first();
    this.removeActionButton = page.locator('button:has-text("Remove"), button:has-text("Delete Action")').first();
    this.actionConfigFields = page.locator('.action-config, .action-parameters').first();
  }

  async expectJobsPage() {
    await expect(this.pageTitle).toBeVisible();
    await expect(this.jobsTable).toBeVisible();
    await expect(this.createJobButton).toBeVisible();
  }

  async clickCreateJob() {
    await this.createJobButton.click();
    await expect(this.createJobModal).toBeVisible();
  }

  async createJob(jobData: {
    name: string;
    description?: string;
    type?: string;
    action?: string;
  }) {
    await this.clickCreateJob();
    await this.jobNameField.fill(jobData.name);
    
    if (jobData.description) {
      await this.jobDescriptionField.fill(jobData.description);
    }
    if (jobData.type) {
      await this.jobTypeSelect.selectOption(jobData.type);
    }
    if (jobData.action) {
      await this.actionSelect.selectOption(jobData.action);
    }
    
    await this.saveJobButton.click();
    await this.waitForPageLoad();
  }

  async executeFirstJob() {
    const firstExecuteButton = this.jobsTable.locator('button:has-text("Execute"), button:has-text("Run")').first();
    await firstExecuteButton.click();
    await this.waitForPageLoad();
  }

  async viewJobHistory() {
    const firstHistoryButton = this.jobsTable.locator('button:has-text("History")').first();
    await firstHistoryButton.click();
    await expect(this.jobHistoryModal).toBeVisible();
  }

  async viewJobResults() {
    const firstResultsButton = this.jobsTable.locator('button:has-text("Results")').first();
    await firstResultsButton.click();
    await expect(this.jobResultsModal).toBeVisible();
  }

  async scheduleJob(scheduleData: {
    type: string;
    cronExpression?: string;
    interval?: string;
    startTime?: string;
  }) {
    await this.scheduleJobButton.click();
    await expect(this.scheduleModal).toBeVisible();
    
    await this.scheduleTypeSelect.selectOption(scheduleData.type);
    
    if (scheduleData.cronExpression) {
      await this.cronExpressionField.fill(scheduleData.cronExpression);
    }
    if (scheduleData.interval) {
      await this.intervalField.fill(scheduleData.interval);
    }
    if (scheduleData.startTime) {
      await this.startTimeField.fill(scheduleData.startTime);
    }
    
    await this.saveScheduleButton.click();
    await this.waitForPageLoad();
  }

  async openActionsWorkspace() {
    await this.actionsWorkspaceButton.click();
    await expect(this.actionsWorkspaceModal).toBeVisible();
  }

  async searchJobs(searchTerm: string) {
    await this.searchField.fill(searchTerm);
    await this.waitForPageLoad();
  }

  async verifyJobExists(jobName: string) {
    await expect(this.jobsTable.locator(`text="${jobName}"`)).toBeVisible();
  }

  async editFirstJob() {
    const firstEditButton = this.jobsTable.locator('button:has-text("Edit"), [aria-label*="edit" i]').first();
    await firstEditButton.click();
    await this.waitForPageLoad();
  }

  async deleteFirstJob() {
    const firstDeleteButton = this.jobsTable.locator('button:has-text("Delete"), [aria-label*="delete" i]').first();
    await firstDeleteButton.click();
    
    // Confirm deletion
    const confirmButton = this.page.locator('button:has-text("Confirm"), button:has-text("Yes"), button:has-text("Delete")').first();
    await confirmButton.click();
    await this.waitForPageLoad();
  }
}