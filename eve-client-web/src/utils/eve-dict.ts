export type RefTypeTagType = 'default' | 'success' | 'warning' | 'error' | 'info'

export type RefTypeView = {
  label: string
  type: RefTypeTagType
}

export const journalRefTypeMap: Record<string, RefTypeView> = {
  market_transaction: { label: '市场交易', type: 'info' },
  market_escrow: { label: '市场买单押金', type: 'warning' },
  broker_fee: { label: '市场中介费', type: 'error' },
  transaction_tax: { label: '市场交易税', type: 'error' },
  player_trading: { label: '玩家直接交易', type: 'success' },
  item_trader_payment: { label: '兑换商付款', type: 'info' },
  market_provider_tax: { label: '设施提供者税', type: 'warning' },

  industry_job_tax: { label: '工业制造税', type: 'warning' },
  industry_facility_tax: { label: '工业设施附加税', type: 'warning' },
  manufacturing: { label: '制造安装费', type: 'error' },
  researching_technology: { label: '发明安装费', type: 'error' },
  researching_time_efficiency: { label: 'TE 研究费', type: 'error' },
  researching_material_efficiency: { label: 'ME 研究费', type: 'error' },
  copying: { label: '蓝图拷贝费', type: 'error' },
  reprocessing_tax: { label: '化矿税', type: 'warning' },

  planetary_import_tax: { label: 'PI 进口海关税', type: 'error' },
  planetary_export_tax: { label: 'PI 出口海关税', type: 'error' },

  contract_price: { label: '合同金额', type: 'info' },
  contract_brokers_fee: { label: '合同发布费', type: 'error' },
  contract_sales_tax: { label: '合同交易税', type: 'error' },
  contract_reward: { label: '合同奖励', type: 'success' },
  contract_collateral: { label: '合同押金扣款', type: 'warning' },
  contract_collateral_payout: { label: '合同押金退还', type: 'success' },
  contract_price_payment_corp: { label: '军团合同付款', type: 'info' },
  corporation_account_withdrawal: { label: '军团账户提现', type: 'default' },
  corporation_dividend_payment: { label: '军团分红', type: 'success' },
  office_rental_fee: { label: '办公室租金', type: 'error' },
  factory_slot_rental_fee: { label: '工厂流水线租金', type: 'error' },

  bounty_prizes: { label: '击杀赏金', type: 'success' },
  bounty_prize_corporation_tax: { label: '赏金军团税', type: 'warning' },
  mission_reward: { label: '任务奖励', type: 'success' },
  mission_time_bonus_reward: { label: '任务限时奖励', type: 'success' },
  agent_donation: { label: '代理人资助', type: 'info' },
  project_discovery_reward: { label: '探索计划奖励', type: 'success' },
  daily_challenge_reward: { label: '日常挑战奖励', type: 'success' },
  daily_goal_payouts: { label: '每日目标奖励', type: 'success' },
  incursion_payout: { label: '入侵统合部奖励', type: 'success' },
  bounty_surcharge: { label: '赏金附加费', type: 'error' },

  insurance: { label: '保险赔付', type: 'success' },
  clone_activation: { label: '克隆体激活费', type: 'error' },
  clone_transfer: { label: '远距克隆费用', type: 'error' },
  jump_clone_activation_fee: { label: '克隆跳跃费', type: 'error' },
  jump_clone_installation_fee: { label: '克隆体安装费', type: 'error' },
  structure_gate_jump: { label: '星桥过路费', type: 'error' },
  asset_safety_recovery_tax: { label: '资产安全取回税', type: 'error' },
  repair_bill: { label: '维修费用', type: 'error' },
  skill_purchase: { label: '直接购买技能', type: 'error' },
  infrastructure_hub_maintenance: { label: 'IHub 维护费', type: 'error' },

  player_donation: { label: '玩家汇款', type: 'success' },
  cspa: { label: 'CSPA 邮件通讯费', type: 'error' },
  war_fee: { label: '宣战费用', type: 'error' },
}

export function translateRefType(refType?: string): RefTypeView {
  if (!refType) {
    return { label: '未知流水', type: 'default' }
  }

  const mapping = journalRefTypeMap[refType]
  if (mapping) {
    return mapping
  }

  const fallbackLabel = refType
    .split('_')
    .filter(Boolean)
    .map((word) => word[0]?.toUpperCase() + word.slice(1))
    .join(' ')

  return { label: fallbackLabel || '未知流水', type: 'default' }
}
