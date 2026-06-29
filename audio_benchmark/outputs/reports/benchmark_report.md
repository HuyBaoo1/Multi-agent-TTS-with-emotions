# Audio Understanding Benchmark Report

This report compares one-pass audio context extraction across selected providers and models.

## Reliability Summary

| provider | model | reliability_score | coverage_score | transcript_quality_score | nonverbal_tag_score | emotion_agreement_score | error_penalty | unsupported_field_penalty |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| elevenlabs | scribe_v2 | 65.0 | 25.0 | 25.0 | 15.0 | 5.0 | 0.0 | 5.0 |
| gemini | gemini-3.1-pro-preview | 53.5 | 22.5 | 22.5 | 7.5 | 4.0 | 3.0 | 0.0 |
| gemini | gemini-3.5-flash | 50.5 | 22.5 | 22.5 | 4.5 | 4.0 | 3.0 | 0.0 |
| openai | gpt-4o-mini-transcribe | -35.0 | 0.0 | 0.0 | 0.0 | 5.0 | 30.0 | 10.0 |

## Model Comparison

| provider | model | total_files | success | errors | skipped | coverage_rate | empty_transcript_rate | api_error_rate | avg_tags_detected |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| elevenlabs | scribe_v2 | 10 | 10 | 0 | 0 | 1.0 | 0.0 | 0.0 | 4.1 |
| gemini | gemini-3.1-pro-preview | 10 | 9 | 1 | 0 | 0.9 | 0.1 | 0.1 | 0.5 |
| gemini | gemini-3.5-flash | 10 | 9 | 1 | 0 | 0.9 | 0.1 | 0.1 | 0.3 |
| openai | gpt-4o-mini-transcribe | 10 | 0 | 10 | 0 | 0.0 | 1.0 | 1.0 | 0.0 |

## Errors And Skips

| provider | model | file_id | status | error |
| --- | --- | --- | --- | --- |
| gemini | gemini-3.1-pro-preview | Ki_p_s_ng_n_y_r_i_s_bi_n_m_t_-_Quang_i_haveasip_vietcetera_podcast_quangdai_thuy_8ad6043e31a2 | error | Gemini did not return parseable JSON |
| gemini | gemini-3.5-flash | Ki_p_s_ng_n_y_r_i_s_bi_n_m_t_-_Quang_i_haveasip_vietcetera_podcast_quangdai_thuy_8ad6043e31a2 | error | Gemini did not return parseable JSON |
| openai | gpt-4o-mini-transcribe | H_m_nay_chia_s_nhanh_m_t_c_u_n_i_v_vi_c_h_c_c_a_B_c_H_48eebb92fb2d | error | RateLimitError: Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, read the docs: https://platform.openai.com/docs/guides/error-codes/api-errors.', 'type': 'insufficient_quota', 'param': None, 'code': 'insufficient_quota'}} |
| openai | gpt-4o-mini-transcribe | Ice_cream_in_India_is_so_strange_you_have_to_beat_it_with_a_hammer_to_eat_it._In_824ae29722e6 | error | RateLimitError: Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, read the docs: https://platform.openai.com/docs/guides/error-codes/api-errors.', 'type': 'insufficient_quota', 'param': None, 'code': 'insufficient_quota'}} |
| openai | gpt-4o-mini-transcribe | Ki_p_s_ng_n_y_r_i_s_bi_n_m_t_-_Quang_i_haveasip_vietcetera_podcast_quangdai_thuy_8ad6043e31a2 | error | RateLimitError: Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, read the docs: https://platform.openai.com/docs/guides/error-codes/api-errors.', 'type': 'insufficient_quota', 'param': None, 'code': 'insufficient_quota'}} |
| openai | gpt-4o-mini-transcribe | L_n_u_g_p_em_ng_i_y_u_yeulanh_binz_vietcetera_podcast_01eaa383acd7 | error | RateLimitError: Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, read the docs: https://platform.openai.com/docs/guides/error-codes/api-errors.', 'type': 'insufficient_quota', 'param': None, 'code': 'insufficient_quota'}} |
| openai | gpt-4o-mini-transcribe | LinusSebastian_shows_MarcelloHernandez_Jimmy_the_Lollipop_Star_FallonTonight_cafb6eb43684 | error | RateLimitError: Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, read the docs: https://platform.openai.com/docs/guides/error-codes/api-errors.', 'type': 'insufficient_quota', 'param': None, 'code': 'insufficient_quota'}} |
| openai | gpt-4o-mini-transcribe | T_i_sao___jennyhuynh__gi_u_vi_c_l_m_content__-_vietcetera_podcast_genz_genztruye_acce78579516 | error | RateLimitError: Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, read the docs: https://platform.openai.com/docs/guides/error-codes/api-errors.', 'type': 'insufficient_quota', 'param': None, 'code': 'insufficient_quota'}} |
| openai | gpt-4o-mini-transcribe | T_nh_y_u_c_th_t_s_quan_tr_ng_hay_kh_ng___To_To_postcard_t_nhy_u_tamtrang_podcast_c7147cdf2d2a | error | RateLimitError: Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, read the docs: https://platform.openai.com/docs/guides/error-codes/api-errors.', 'type': 'insufficient_quota', 'param': None, 'code': 'insufficient_quota'}} |
| openai | gpt-4o-mini-transcribe | This_was_BAD_shorts_funny_fail_7e67c146fbe9 | error | RateLimitError: Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, read the docs: https://platform.openai.com/docs/guides/error-codes/api-errors.', 'type': 'insufficient_quota', 'param': None, 'code': 'insufficient_quota'}} |
| openai | gpt-4o-mini-transcribe | Tran_Thanh_is_crazy_about_the_boy_Marcus_Pham_because_of_his_adorable_speaking_t_0eb26e6b6fa3 | error | RateLimitError: Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, read the docs: https://platform.openai.com/docs/guides/error-codes/api-errors.', 'type': 'insufficient_quota', 'param': None, 'code': 'insufficient_quota'}} |
| openai | gpt-4o-mini-transcribe | n_h_t_ki_p_n_y_t_i_v_n_mu_n_Hari_Won_l_m_v_c_a_t_i__Tr_n_Th_nh_m_n_l_i_t_t_nh_v__5deca042f3c0 | error | RateLimitError: Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, read the docs: https://platform.openai.com/docs/guides/error-codes/api-errors.', 'type': 'insufficient_quota', 'param': None, 'code': 'insufficient_quota'}} |
