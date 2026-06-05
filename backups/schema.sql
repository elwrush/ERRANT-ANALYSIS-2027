


SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


COMMENT ON SCHEMA "public" IS 'standard public schema';

































CREATE OR REPLACE FUNCTION "public"."calculate_overall_cefr"("p_student_id" "text", "p_assessment_type" "text", "p_exam_type" "text") RETURNS "text"
    LANGUAGE "plpgsql"
    AS $$
DECLARE
  v_listening_cefr TEXT;
  v_reading_cefr TEXT;
  v_writing_cefr TEXT;
  v_speaking_cefr TEXT;
  v_sum NUMERIC := 0;
  v_count INTEGER := 0;
  v_avg NUMERIC;
BEGIN
  -- Get most recent CEFR for Listening
  SELECT cefr INTO v_listening_cefr
  FROM student_submissions
  WHERE student_id = p_student_id
    AND assessment_type = p_assessment_type
    AND exam_type = p_exam_type
    AND skill = 'Listening'
    AND cefr IS NOT NULL
    AND cefr != 'NA'
  ORDER BY submission_date DESC
  LIMIT 1;

  -- Get most recent CEFR for Reading
  SELECT cefr INTO v_reading_cefr
  FROM student_submissions
  WHERE student_id = p_student_id
    AND assessment_type = p_assessment_type
    AND exam_type = p_exam_type
    AND skill = 'Reading'
    AND cefr IS NOT NULL
    AND cefr != 'NA'
  ORDER BY submission_date DESC
  LIMIT 1;

  -- Get most recent CEFR for Writing
  SELECT cefr INTO v_writing_cefr
  FROM student_submissions
  WHERE student_id = p_student_id
    AND assessment_type = p_assessment_type
    AND exam_type = p_exam_type
    AND skill = 'Writing'
    AND cefr IS NOT NULL
    AND cefr != 'NA'
  ORDER BY submission_date DESC
  LIMIT 1;

  -- Get most recent CEFR for Speaking
  SELECT cefr INTO v_speaking_cefr
  FROM student_submissions
  WHERE student_id = p_student_id
    AND assessment_type = p_assessment_type
    AND exam_type = p_exam_type
    AND skill = 'Speaking'
    AND cefr IS NOT NULL
    AND cefr != 'NA'
  ORDER BY submission_date DESC
  LIMIT 1;

  -- Calculate sum and count (excluding Use of English)
  IF v_listening_cefr IS NOT NULL THEN
    v_sum := v_sum + cefr_to_number(v_listening_cefr);
    v_count := v_count + 1;
  END IF;

  IF v_reading_cefr IS NOT NULL THEN
    v_sum := v_sum + cefr_to_number(v_reading_cefr);
    v_count := v_count + 1;
  END IF;

  IF v_writing_cefr IS NOT NULL THEN
    v_sum := v_sum + cefr_to_number(v_writing_cefr);
    v_count := v_count + 1;
  END IF;

  IF v_speaking_cefr IS NOT NULL THEN
    v_sum := v_sum + cefr_to_number(v_speaking_cefr);
    v_count := v_count + 1;
  END IF;

  -- Return NULL if no skills found
  IF v_count = 0 THEN
    RETURN NULL;
  END IF;

  -- Calculate average and convert back to CEFR
  v_avg := v_sum / v_count;
  RETURN number_to_cefr(v_avg);
END;
$$;


ALTER FUNCTION "public"."calculate_overall_cefr"("p_student_id" "text", "p_assessment_type" "text", "p_exam_type" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."cefr_to_number"("cefr_level" "text") RETURNS integer
    LANGUAGE "plpgsql" IMMUTABLE
    AS $$
BEGIN
  RETURN CASE cefr_level
    WHEN 'A1' THEN 1
    WHEN 'A1+' THEN 2
    WHEN 'A2' THEN 3
    WHEN 'A2+' THEN 4
    WHEN 'B1' THEN 5
    WHEN 'B1+' THEN 6
    WHEN 'B2' THEN 7
    WHEN 'B2+' THEN 8
    WHEN 'C1' THEN 9
    WHEN 'C1+' THEN 10
    WHEN 'C2' THEN 11
    ELSE NULL
  END;
END;
$$;


ALTER FUNCTION "public"."cefr_to_number"("cefr_level" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."claim_student_id"("id_to_claim" "text") RETURNS "text"
    LANGUAGE "plpgsql"
    AS $$
DECLARE
  current_user_student_id TEXT;
  is_id_already_claimed BOOLEAN;
BEGIN
  -- 1. Check if the currently logged-in user already has a student_id in their profile.
  SELECT student_id INTO current_user_student_id
  FROM public.profiles
  WHERE id = auth.uid();

  IF current_user_student_id IS NOT NULL THEN
    RETURN 'Error: Your account is already linked to a Student ID.';
  END IF;

  -- 2. Check if the student_id they want to claim has been taken by anyone.
  SELECT EXISTS (
    SELECT 1
    FROM public.profiles
    WHERE student_id = id_to_claim
  ) INTO is_id_already_claimed;

  IF is_id_already_claimed THEN
    RETURN 'Error: This Student ID has already been claimed by another user.';
  END IF;

  -- 3. If all checks pass, update the user's profile with the new student_id.
  UPDATE public.profiles
  SET student_id = id_to_claim
  WHERE id = auth.uid();

  RETURN 'Success: Your Student ID has been linked to your account.';
END;
$$;


ALTER FUNCTION "public"."claim_student_id"("id_to_claim" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."escape_sql_text"("input_text" "text") RETURNS "text"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    -- Escape single quotes by doubling them (standard SQL escaping)
    -- This is the correct way: replace ' with ''
    input_text := REPLACE(input_text, '''', '''''');
    
    RETURN input_text;
END;
$$;


ALTER FUNCTION "public"."escape_sql_text"("input_text" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."handle_new_user"() RETURNS "trigger"
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
BEGIN
  -- Insert a new row into the public.profiles table for the new user.
  INSERT INTO public.profiles (id, nickname, email)
  VALUES (new.id, new.raw_user_meta_data->>'nickname', new.email);
  RETURN new;
END;
$$;


ALTER FUNCTION "public"."handle_new_user"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."insert_speaking_assessment"("p_student_id" integer, "p_skill" "text", "p_assessment_type" "text", "p_exam_question" "text", "p_exam_type" "text", "p_student_text" "text", "p_url" "text", "p_word_count" integer, "p_overall_score" integer, "p_cefr_level" "text", "p_speaking_grammar_vocab_score" integer, "p_speaking_discourse_management_score" integer, "p_speaking_pron_score" integer, "p_speaking_interactive_communication_score" integer, "p_speaking_summary" "text", "p_speaking_grammar_vocab_comment" "text", "p_speaking_discourse_management_comment" "text", "p_speaking_pron_comment" "text", "p_speaking_interactive_communication_comment" "text") RETURNS integer
    LANGUAGE "plpgsql"
    AS $$
DECLARE
  result_id INTEGER;
BEGIN
  INSERT INTO student_submissions (
    student_id, skill, assessment_type, exam_question, exam_type,
    student_text, url, word_count, overall_score, cefr_level,
    speaking_grammar_vocab_score, speaking_discourse_management_score,
    speaking_pron_score, speaking_interactive_communication_score,
    speaking_summary, speaking_grammar_vocab_comment,
    speaking_discourse_management_comment, speaking_pron_comment,
    speaking_interactive_communication_comment
  ) VALUES (
    p_student_id, p_skill, p_assessment_type, p_exam_question, p_exam_type,
    p_student_text, p_url, p_word_count, p_overall_score, p_cefr_level,
    p_speaking_grammar_vocab_score, p_speaking_discourse_management_score,
    p_speaking_pron_score, p_speaking_interactive_communication_score,
    p_speaking_summary, p_speaking_grammar_vocab_comment,
    p_speaking_discourse_management_comment, p_speaking_pron_comment,
    p_speaking_interactive_communication_comment
  )
  RETURNING id INTO result_id;
  
  RETURN result_id;
END;
$$;


ALTER FUNCTION "public"."insert_speaking_assessment"("p_student_id" integer, "p_skill" "text", "p_assessment_type" "text", "p_exam_question" "text", "p_exam_type" "text", "p_student_text" "text", "p_url" "text", "p_word_count" integer, "p_overall_score" integer, "p_cefr_level" "text", "p_speaking_grammar_vocab_score" integer, "p_speaking_discourse_management_score" integer, "p_speaking_pron_score" integer, "p_speaking_interactive_communication_score" integer, "p_speaking_summary" "text", "p_speaking_grammar_vocab_comment" "text", "p_speaking_discourse_management_comment" "text", "p_speaking_pron_comment" "text", "p_speaking_interactive_communication_comment" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."insert_writing_assessment"("p_student_id" integer, "p_skill" "text", "p_assessment_type" "text", "p_exam_question" "text", "p_exam_type" "text", "p_student_text" "text", "p_word_count" integer, "p_overall_score" integer, "p_cefr_level" "text", "p_content_score" integer, "p_communicative_achievement_score" integer, "p_organisation_score" integer, "p_language_score" integer, "p_summary_comment" "text", "p_content_feedback" "text", "p_communicative_achievement_feedback" "text", "p_organisation_feedback" "text", "p_language_feedback" "text") RETURNS integer
    LANGUAGE "plpgsql"
    AS $$
DECLARE
  result_id INTEGER;
BEGIN
  INSERT INTO student_submissions (
    student_id, skill, assessment_type, exam_question, exam_type,
    student_text, word_count, overall_score, cefr_level,
    content_score, communicative_achievement_score, organisation_score, language_score,
    summary_comment, content_feedback, communicative_achievement_feedback,
    organisation_feedback, language_feedback
  ) VALUES (
    p_student_id, p_skill, p_assessment_type, p_exam_question, p_exam_type,
    p_student_text, p_word_count, p_overall_score, p_cefr_level,
    p_content_score, p_communicative_achievement_score, p_organisation_score, p_language_score,
    p_summary_comment, p_content_feedback, p_communicative_achievement_feedback,
    p_organisation_feedback, p_language_feedback
  )
  RETURNING id INTO result_id;
  
  RETURN result_id;
END;
$$;


ALTER FUNCTION "public"."insert_writing_assessment"("p_student_id" integer, "p_skill" "text", "p_assessment_type" "text", "p_exam_question" "text", "p_exam_type" "text", "p_student_text" "text", "p_word_count" integer, "p_overall_score" integer, "p_cefr_level" "text", "p_content_score" integer, "p_communicative_achievement_score" integer, "p_organisation_score" integer, "p_language_score" integer, "p_summary_comment" "text", "p_content_feedback" "text", "p_communicative_achievement_feedback" "text", "p_organisation_feedback" "text", "p_language_feedback" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."insert_writing_evaluation"("payload" "jsonb") RETURNS integer
    LANGUAGE "plpgsql"
    AS $$
DECLARE
  new_submission_id integer;
BEGIN
  INSERT INTO public.student_submissions (
    student_id,
    student_text,
    exam_question,
    word_count,
    skill,
    assessment_type,
    exam_type,
    cefr_level,
    content_score,
    communicative_achievement_score,
    organisation_score,
    language_score,
    overall_score,
    content_feedback,
    communicative_achievement_feedback,
    organisation_feedback,
    language_feedback,
    summary_comment,
    writing_submission
  )
  VALUES (
    payload->>'student_id',
    payload->>'student_text',
    payload->>'exam_question',
    (payload->>'word_count')::integer,
    'Writing',
    payload->>'assessment_type',
    payload->>'exam_type',
    payload->>'cefr_level',
    (payload->'scores'->>'content')::numeric,
    (payload->'scores'->>'communicative_achievement')::numeric,
    (payload->'scores'->>'organisation')::numeric,
    (payload->'scores'->>'language')::numeric,
    (payload->'scores'->>'overall')::numeric,
    payload->'feedback'->>'content',
    payload->'feedback'->>'communicative_achievement',
    payload->'feedback'->>'organisation',
    payload->'feedback'->>'language',
    payload->'feedback'->>'summary',
    payload
  )
  RETURNING id INTO new_submission_id;

  RETURN new_submission_id;
END;
$$;


ALTER FUNCTION "public"."insert_writing_evaluation"("payload" "jsonb") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."number_to_cefr"("num_value" numeric) RETURNS "text"
    LANGUAGE "plpgsql" IMMUTABLE
    AS $$
BEGIN
  RETURN CASE ROUND(num_value)::INTEGER
    WHEN 1 THEN 'A1'
    WHEN 2 THEN 'A1+'
    WHEN 3 THEN 'A2'
    WHEN 4 THEN 'A2+'
    WHEN 5 THEN 'B1'
    WHEN 6 THEN 'B1+'
    WHEN 7 THEN 'B2'
    WHEN 8 THEN 'B2+'
    WHEN 9 THEN 'C1'
    WHEN 10 THEN 'C1+'
    WHEN 11 THEN 'C2'
    ELSE NULL
  END;
END;
$$;


ALTER FUNCTION "public"."number_to_cefr"("num_value" numeric) OWNER TO "postgres";


CREATE PROCEDURE "public"."safe_insert_student_submission"(IN "p_student_id" "text", IN "p_skill" "text", IN "p_assessment_type" "text", IN "p_exam_question" "text", IN "p_exam_type" "text", IN "p_student_text" "text", IN "p_word_count" integer, IN "p_overall_score" numeric, IN "p_cefr_level" "text", IN "p_content_score" numeric, IN "p_communicative_achievement_score" numeric, IN "p_organisation_score" numeric, IN "p_language_score" numeric, IN "p_summary_comment" "text", IN "p_content_feedback" "text", IN "p_communicative_achievement_feedback" "text", IN "p_organisation_feedback" "text", IN "p_language_feedback" "text")
    LANGUAGE "plpgsql"
    AS $$
DECLARE
    new_id INTEGER;
BEGIN
    -- Automatically escape all text parameters
    p_student_text := REPLACE(p_student_text, '''', '''''');
    p_summary_comment := REPLACE(p_summary_comment, '''', '''''');
    p_content_feedback := REPLACE(p_content_feedback, '''', '''''');
    p_communicative_achievement_feedback := REPLACE(p_communicative_achievement_feedback, '''', '''''');
    p_organisation_feedback := REPLACE(p_organisation_feedback, '''', '''''');
    p_language_feedback := REPLACE(p_language_feedback, '''', '''''');
    
    -- Execute the safe insert
    INSERT INTO public.student_submissions (
        student_id, skill, assessment_type, exam_question, exam_type,
        student_text, word_count, overall_score, cefr_level,
        content_score, communicative_achievement_score, organisation_score, language_score,
        summary_comment, content_feedback, communicative_achievement_feedback,
        organisation_feedback, language_feedback
    ) VALUES (
        p_student_id, p_skill, p_assessment_type, p_exam_question, p_exam_type,
        p_student_text, p_word_count, p_overall_score, p_cefr_level,
        p_content_score, p_communicative_achievement_score, p_organisation_score, p_language_score,
        p_summary_comment, p_content_feedback, p_communicative_achievement_feedback,
        p_organisation_feedback, p_language_feedback
    ) RETURNING id INTO new_id;
    
    RAISE NOTICE 'Successfully inserted record with ID: %', new_id;
END;
$$;


ALTER PROCEDURE "public"."safe_insert_student_submission"(IN "p_student_id" "text", IN "p_skill" "text", IN "p_assessment_type" "text", IN "p_exam_question" "text", IN "p_exam_type" "text", IN "p_student_text" "text", IN "p_word_count" integer, IN "p_overall_score" numeric, IN "p_cefr_level" "text", IN "p_content_score" numeric, IN "p_communicative_achievement_score" numeric, IN "p_organisation_score" numeric, IN "p_language_score" numeric, IN "p_summary_comment" "text", IN "p_content_feedback" "text", IN "p_communicative_achievement_feedback" "text", IN "p_organisation_feedback" "text", IN "p_language_feedback" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."update_overall_cefr_trigger"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
DECLARE
  v_overall_cefr TEXT;
BEGIN
  -- Calculate overall CEFR for this student/assessment
  v_overall_cefr := calculate_overall_cefr(
    NEW.student_id,
    NEW.assessment_type,
    NEW.exam_type
  );

  -- Update overall_cefr on the CURRENT record being inserted/updated
  NEW.overall_cefr := v_overall_cefr;

  RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."update_overall_cefr_trigger"() OWNER TO "postgres";

SET default_tablespace = '';

SET default_table_access_method = "heap";


CREATE TABLE IF NOT EXISTS "public"."cefr_levels" (
    "level" character varying(3) NOT NULL,
    "description" "text"
);


ALTER TABLE "public"."cefr_levels" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."classlists" (
    "student_id" "text" NOT NULL,
    "name" "text" NOT NULL,
    "class" "text" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "timezone"('Asia/Bangkok'::"text", "now"()) NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "timezone"('Asia/Bangkok'::"text", "now"()) NOT NULL,
    "user_id" "uuid" DEFAULT "auth"."uid"()
);


ALTER TABLE "public"."classlists" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."egp_statements" (
    "id" "text" NOT NULL,
    "statement" "text" NOT NULL,
    "supercategory" "text" NOT NULL,
    "subcategory" "text" NOT NULL,
    "level" "text" NOT NULL,
    "example" "text"
);


ALTER TABLE "public"."egp_statements" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."error_reports" (
    "id" bigint NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "student_id" "text" NOT NULL,
    "class" "text" NOT NULL,
    "name" "text" NOT NULL,
    "error_percent" integer,
    "summary" "text" NOT NULL,
    "r_noun" integer DEFAULT 0,
    "r_noun_num" integer DEFAULT 0,
    "r_noun_poss" integer DEFAULT 0,
    "r_noun_infl" integer DEFAULT 0,
    "r_verb" integer DEFAULT 0,
    "r_verb_tense" integer DEFAULT 0,
    "r_verb_sva" integer DEFAULT 0,
    "r_verb_form" integer DEFAULT 0,
    "r_verb_infl" integer DEFAULT 0,
    "r_adj" integer DEFAULT 0,
    "r_adj_form" integer DEFAULT 0,
    "r_adv" integer DEFAULT 0,
    "r_prep" integer DEFAULT 0,
    "r_pron" integer DEFAULT 0,
    "r_det" integer DEFAULT 0,
    "r_conj" integer DEFAULT 0,
    "r_part" integer DEFAULT 0,
    "r_punct" integer DEFAULT 0,
    "r_spell" integer DEFAULT 0,
    "r_orth" integer DEFAULT 0,
    "r_morph" integer DEFAULT 0,
    "r_wo" integer DEFAULT 0,
    "r_contr" integer DEFAULT 0,
    "m_noun" integer DEFAULT 0,
    "m_noun_num" integer DEFAULT 0,
    "m_verb" integer DEFAULT 0,
    "m_verb_tense" integer DEFAULT 0,
    "m_verb_form" integer DEFAULT 0,
    "m_prep" integer DEFAULT 0,
    "m_pron" integer DEFAULT 0,
    "m_det" integer DEFAULT 0,
    "m_conj" integer DEFAULT 0,
    "m_part" integer DEFAULT 0,
    "m_punct" integer DEFAULT 0,
    "u_noun" integer DEFAULT 0,
    "u_verb" integer DEFAULT 0,
    "u_prep" integer DEFAULT 0,
    "u_pron" integer DEFAULT 0,
    "u_det" integer DEFAULT 0,
    "u_conj" integer DEFAULT 0,
    "u_part" integer DEFAULT 0,
    "u_punct" integer DEFAULT 0,
    "other" integer DEFAULT 0,
    "unk" integer DEFAULT 0,
    "word_count" integer,
    "academic_year" integer DEFAULT 2007,
    "date" "date"
);


ALTER TABLE "public"."error_reports" OWNER TO "postgres";


COMMENT ON TABLE "public"."error_reports" IS 'Tracks errors made by students';



COMMENT ON COLUMN "public"."error_reports"."word_count" IS 'Number of words in a submission';



COMMENT ON COLUMN "public"."error_reports"."academic_year" IS 'The current Academic Year';



CREATE TABLE IF NOT EXISTS "public"."error_reports_backup" (
    "id" bigint,
    "created_at" timestamp with time zone,
    "student_id" "text",
    "class" "text",
    "name" "text",
    "error_percent" integer,
    "summary" "text",
    "r_noun" integer,
    "r_noun_num" integer,
    "r_noun_poss" integer,
    "r_noun_infl" integer,
    "r_verb" integer,
    "r_verb_tense" integer,
    "r_verb_sva" integer,
    "r_verb_form" integer,
    "r_verb_infl" integer,
    "r_adj" integer,
    "r_adj_form" integer,
    "r_adv" integer,
    "r_prep" integer,
    "r_pron" integer,
    "r_det" integer,
    "r_conj" integer,
    "r_part" integer,
    "r_punct" integer,
    "r_spell" integer,
    "r_orth" integer,
    "r_morph" integer,
    "r_wo" integer,
    "r_contr" integer,
    "m_noun" integer,
    "m_noun_num" integer,
    "m_verb" integer,
    "m_verb_tense" integer,
    "m_verb_form" integer,
    "m_prep" integer,
    "m_pron" integer,
    "m_det" integer,
    "m_conj" integer,
    "m_part" integer,
    "m_punct" integer,
    "u_noun" integer,
    "u_verb" integer,
    "u_prep" integer,
    "u_pron" integer,
    "u_det" integer,
    "u_conj" integer,
    "u_part" integer,
    "u_punct" integer,
    "other" integer,
    "unk" integer,
    "word_count" integer,
    "academic_year" integer,
    "date" "date"
);


ALTER TABLE "public"."error_reports_backup" OWNER TO "postgres";


ALTER TABLE "public"."error_reports" ALTER COLUMN "id" ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME "public"."error_reports_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);



CREATE TABLE IF NOT EXISTS "public"."linguistic_features" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "text_id" "uuid",
    "features" "jsonb",
    "analysis_metadata" "jsonb",
    "user_id" "uuid"
);


ALTER TABLE "public"."linguistic_features" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."profiles" (
    "id" "uuid" NOT NULL,
    "email" "text",
    "student_id" "text",
    "nickname" "text",
    "class" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "role" "text" DEFAULT 'student'::"text"
);


ALTER TABLE "public"."profiles" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."reading_lab_student_answers" (
    "student_id" character varying(255) NOT NULL,
    "test_paper" character varying(255) NOT NULL,
    "score" integer,
    "qu1" integer,
    "qu2" integer,
    "qu3" integer,
    "qu4" integer,
    "qu5" integer,
    "qu6" integer,
    "qu7" integer,
    "qu8" integer,
    "qu9" integer,
    "qu10" integer,
    "qu11" integer,
    "qu12" integer,
    "submitted_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."reading_lab_student_answers" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."reports" (
    "id" integer NOT NULL,
    "student_id" integer NOT NULL,
    "report_data" "text" NOT NULL,
    "created_at" timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE "public"."reports" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."reports_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE "public"."reports_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."reports_id_seq" OWNED BY "public"."reports"."id";



CREATE TABLE IF NOT EXISTS "public"."student_submissions" (
    "id" integer NOT NULL,
    "student_id" "text" NOT NULL,
    "submission_date" timestamp with time zone DEFAULT "timezone"('Asia/Bangkok'::"text", "now"()) NOT NULL,
    "topic" "text",
    "student_text" "text",
    "word_count" integer,
    "overall_score" numeric(4,1),
    "summary_comment" "text",
    "content_feedback" "text",
    "communicative_achievement_feedback" "text",
    "organisation_feedback" "text",
    "language_feedback" "text",
    "content_score" numeric(3,1),
    "communicative_achievement_score" numeric(3,1),
    "organisation_score" numeric(3,1),
    "language_score" numeric(3,1),
    "skill" "text",
    "assessment_type" "text" DEFAULT 'Formative'::"text",
    "exam_type" "text" DEFAULT 'PET'::"text",
    "speaking_grammar_vocab_score" numeric,
    "speaking_discourse_management_score" numeric,
    "speaking_pron_score" numeric,
    "speaking_interactive_communication_score" numeric,
    "speaking_grammar_vocab_comment" "text",
    "speaking_discourse_management_comment" "text",
    "speaking_pron_comment" "text",
    "speaking_interactive_communication_comment" "text",
    "teacher_global_achievement_comment" "text",
    "speaking_summary" "text",
    "user_id" "uuid",
    "reading_score" numeric,
    "reading_average" numeric,
    "reading_comment" "text",
    "listening_score" numeric,
    "listening_average" numeric,
    "listening_comment" "text",
    "writing_submission" "jsonb",
    "url" "text",
    "overall_cefr" "text",
    "use_of_english_score" numeric,
    "use_of_english_average" numeric,
    "use_of_english_comment" "text",
    "cefr" "text",
    "errors" numeric,
    "academic_year" integer NOT NULL,
    CONSTRAINT "student_submissions_academic_year_check" CHECK ((("academic_year" >= 2000) AND ("academic_year" <= 2100))),
    CONSTRAINT "student_submissions_assessment_type_check" CHECK (("assessment_type" = ANY (ARRAY['Formative'::"text", 'Term 1 Midterm'::"text", 'Term 1 Finals'::"text", 'Term 2 Midterm'::"text", 'Term 2 Finals'::"text", 'CA'::"text", 'Benchmark'::"text"]))),
    CONSTRAINT "student_submissions_cefr_check" CHECK ((("cefr" IS NULL) OR ("cefr" = ANY (ARRAY['NA'::"text", 'A1'::"text", 'A1+'::"text", 'A2'::"text", 'A2+'::"text", 'B1'::"text", 'B1+'::"text", 'B2'::"text", 'B2+'::"text", 'C1'::"text", 'C1+'::"text", 'C2'::"text"])))),
    CONSTRAINT "student_submissions_exam_type_check" CHECK (("exam_type" = ANY (ARRAY['Flyers'::"text", 'Movers'::"text", 'KEY'::"text", 'PET'::"text", 'IELTS'::"text", 'FIRST'::"text"])))
);


ALTER TABLE "public"."student_submissions" OWNER TO "postgres";


COMMENT ON COLUMN "public"."student_submissions"."errors" IS 'Show the number of errors a student makes in their writing';



CREATE SEQUENCE IF NOT EXISTS "public"."student_submissions_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE "public"."student_submissions_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."student_submissions_id_seq" OWNED BY "public"."student_submissions"."id";



CREATE TABLE IF NOT EXISTS "public"."student_submissions_writing_ielts" (
    "student_id" "text" NOT NULL,
    "submission_date" timestamp with time zone DEFAULT "timezone"('Asia/Bangkok'::"text", "now"()) NOT NULL,
    "academic_year" integer NOT NULL,
    "user_id" "uuid",
    "topic" "text",
    "student_text" "text",
    "word_count" integer,
    "overall_score" numeric(4,1),
    "summary_comment" "text",
    "skill" "text" DEFAULT 'Writing'::"text",
    "assessment_type" "text",
    "task" "text",
    "task_response_score" numeric(3,1),
    "task_response_feedback" "text",
    "task_achievement_score" numeric(3,1),
    "task_achievement_feedback" "text",
    "coherence_cohesion_score" numeric(3,1),
    "coherence_cohesion_feedback" "text",
    "lexical_resource_score" numeric(3,1),
    "lexical_resource_feedback" "text",
    "grammatical_range_score" numeric(3,1),
    "grammatical_range_feedback" "text",
    CONSTRAINT "student_submissions_writing_ielts_academic_year_check" CHECK ((("academic_year" >= 2000) AND ("academic_year" <= 2100))),
    CONSTRAINT "student_submissions_writing_ielts_assessment_type_check" CHECK (("assessment_type" = ANY (ARRAY['Formative'::"text", 'Term 1 Midterm'::"text", 'Term 1 Finals'::"text", 'Term 2 Midterm'::"text", 'Term 2 Finals'::"text", 'CA'::"text", 'Benchmark'::"text"]))),
    CONSTRAINT "student_submissions_writing_ielts_task_check" CHECK (("task" = ANY (ARRAY['Task 1'::"text", 'Task 2'::"text"])))
);


ALTER TABLE "public"."student_submissions_writing_ielts" OWNER TO "postgres";


COMMENT ON TABLE "public"."student_submissions_writing_ielts" IS 'Stores writing assessment submissions for IELTS Academic Training. Primary key is composite (student_id, submission_date) to allow multiple submissions per student. Note: IELTS does not report CEFR levels.';



COMMENT ON COLUMN "public"."student_submissions_writing_ielts"."student_id" IS 'Student identifier (e.g., "S12345")';



COMMENT ON COLUMN "public"."student_submissions_writing_ielts"."submission_date" IS 'Timestamp when the submission was recorded (Bangkok timezone)';



COMMENT ON COLUMN "public"."student_submissions_writing_ielts"."academic_year" IS 'Academic year (e.g., 2026)';



COMMENT ON COLUMN "public"."student_submissions_writing_ielts"."user_id" IS 'Reference to auth.users table (teacher/admin who entered data)';



COMMENT ON COLUMN "public"."student_submissions_writing_ielts"."overall_score" IS 'Overall IELTS band score (0.0 - 9.0)';



COMMENT ON COLUMN "public"."student_submissions_writing_ielts"."task" IS 'IELTS writing task: Task 1 (report) or Task 2 (essay)';



CREATE TABLE IF NOT EXISTS "public"."text_samples" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "content" "text" NOT NULL,
    "cefr_level" character varying(3),
    "text_type" character varying(50),
    "topic" character varying(100),
    "word_count" integer,
    "source_url" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "user_id" "uuid"
);


ALTER TABLE "public"."text_samples" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."writing_assessment_cambridge" (
    "student_id" "text" NOT NULL,
    "submission_date" timestamp with time zone DEFAULT "timezone"('Asia/Bangkok'::"text", "now"()) NOT NULL,
    "academic_year" integer NOT NULL,
    "topic" "text",
    "student_text" "text",
    "word_count" integer,
    "overall_score" numeric(4,1),
    "summary_comment" "text",
    "cefr" "text",
    "skill" "text" DEFAULT 'Writing'::"text",
    "assessment_type" "text",
    "exam_type" "text",
    "task" "text",
    "content_score" numeric(3,1),
    "content_feedback" "text",
    "communicative_achievement_score" numeric(3,1),
    "communicative_achievement_feedback" "text",
    "organisation_score" numeric(3,1),
    "organisation_feedback" "text",
    "language_score" numeric(3,1),
    "language_feedback" "text",
    "error_count" numeric(5,2),
    "error_types" "jsonb",
    CONSTRAINT "student_submissions_writing_cambridge_academic_year_check" CHECK ((("academic_year" >= 2000) AND ("academic_year" <= 2100))),
    CONSTRAINT "student_submissions_writing_cambridge_assessment_type_check" CHECK (("assessment_type" = ANY (ARRAY['Formative'::"text", 'Term 1 Midterm'::"text", 'Term 1 Finals'::"text", 'Term 2 Midterm'::"text", 'Term 2 Finals'::"text", 'CA'::"text", 'Benchmark'::"text"]))),
    CONSTRAINT "student_submissions_writing_cambridge_cefr_check" CHECK (("cefr" = ANY (ARRAY['NA'::"text", 'A1'::"text", 'A1+'::"text", 'A2'::"text", 'A2+'::"text", 'B1'::"text", 'B1+'::"text", 'B2'::"text", 'B2+'::"text", 'C1'::"text", 'C1+'::"text", 'C2'::"text"]))),
    CONSTRAINT "student_submissions_writing_cambridge_exam_type_check" CHECK (("exam_type" = ANY (ARRAY['KEY'::"text", 'PET'::"text", 'FIRST'::"text"]))),
    CONSTRAINT "student_submissions_writing_cambridge_task_check" CHECK (("task" = ANY (ARRAY['Part 1'::"text", 'Part 2'::"text"])))
);


ALTER TABLE "public"."writing_assessment_cambridge" OWNER TO "postgres";


COMMENT ON TABLE "public"."writing_assessment_cambridge" IS 'Stores writing assessment submissions for Cambridge exams (KEY, PET, FIRST). Primary key is composite (student_id, submission_date) to allow multiple submissions per student.';



COMMENT ON COLUMN "public"."writing_assessment_cambridge"."student_id" IS 'Student identifier (e.g., "S12345")';



COMMENT ON COLUMN "public"."writing_assessment_cambridge"."submission_date" IS 'Timestamp when the submission was recorded (Bangkok timezone)';



COMMENT ON COLUMN "public"."writing_assessment_cambridge"."academic_year" IS 'Academic year (e.g., 2026)';



COMMENT ON COLUMN "public"."writing_assessment_cambridge"."cefr" IS 'CEFR level assessed for Cambridge exams';



COMMENT ON COLUMN "public"."writing_assessment_cambridge"."exam_type" IS 'Type of Cambridge exam: KEY, PET, or FIRST';



COMMENT ON COLUMN "public"."writing_assessment_cambridge"."task" IS 'Writing task part: Part 1 or Part 2';



COMMENT ON COLUMN "public"."writing_assessment_cambridge"."error_count" IS 'Grammatical error count per 100 words (calculated via ERRANT). 
Lower is better. NULL means not yet analyzed.';



COMMENT ON COLUMN "public"."writing_assessment_cambridge"."error_types" IS 'JSON object containing detailed error type breakdown from ERRANT analysis.
Includes total_errors, error_count_per_100, errors_by_type, and individual edits.';



ALTER TABLE ONLY "public"."reports" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."reports_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."student_submissions" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."student_submissions_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."cefr_levels"
    ADD CONSTRAINT "cefr_levels_pkey" PRIMARY KEY ("level");



ALTER TABLE ONLY "public"."classlists"
    ADD CONSTRAINT "classlists_pkey" PRIMARY KEY ("student_id");



ALTER TABLE ONLY "public"."egp_statements"
    ADD CONSTRAINT "egp_statements_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."error_reports"
    ADD CONSTRAINT "error_reports_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."error_reports"
    ADD CONSTRAINT "error_reports_student_date_unique" UNIQUE ("student_id", "date");



ALTER TABLE ONLY "public"."linguistic_features"
    ADD CONSTRAINT "linguistic_features_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."profiles"
    ADD CONSTRAINT "profiles_email_key" UNIQUE ("email");



ALTER TABLE ONLY "public"."profiles"
    ADD CONSTRAINT "profiles_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."profiles"
    ADD CONSTRAINT "profiles_student_id_key" UNIQUE ("student_id");



ALTER TABLE ONLY "public"."reading_lab_student_answers"
    ADD CONSTRAINT "reading_lab_student_answers_pkey" PRIMARY KEY ("student_id", "test_paper", "submitted_at");



ALTER TABLE ONLY "public"."reports"
    ADD CONSTRAINT "reports_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."student_submissions"
    ADD CONSTRAINT "student_submissions_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."writing_assessment_cambridge"
    ADD CONSTRAINT "student_submissions_writing_cambridge_pkey" PRIMARY KEY ("student_id", "submission_date");



ALTER TABLE ONLY "public"."student_submissions_writing_ielts"
    ADD CONSTRAINT "student_submissions_writing_ielts_pkey" PRIMARY KEY ("student_id", "submission_date");



ALTER TABLE ONLY "public"."text_samples"
    ADD CONSTRAINT "text_samples_pkey" PRIMARY KEY ("id");



CREATE INDEX "idx_cambridge_academic_year" ON "public"."writing_assessment_cambridge" USING "btree" ("academic_year");



CREATE INDEX "idx_cambridge_cefr" ON "public"."writing_assessment_cambridge" USING "btree" ("cefr") WHERE ("cefr" IS NOT NULL);



CREATE INDEX "idx_cambridge_error_count" ON "public"."writing_assessment_cambridge" USING "btree" ("error_count") WHERE ("error_count" IS NOT NULL);



CREATE INDEX "idx_cambridge_exam_type" ON "public"."writing_assessment_cambridge" USING "btree" ("exam_type");



CREATE INDEX "idx_cambridge_student_id" ON "public"."writing_assessment_cambridge" USING "btree" ("student_id");



CREATE INDEX "idx_egp_level" ON "public"."egp_statements" USING "btree" ("level");



CREATE INDEX "idx_egp_subcategory" ON "public"."egp_statements" USING "btree" ("subcategory");



CREATE INDEX "idx_egp_super_sub" ON "public"."egp_statements" USING "btree" ("supercategory", "subcategory");



CREATE INDEX "idx_egp_supercategory" ON "public"."egp_statements" USING "btree" ("supercategory");



CREATE INDEX "idx_ielts_academic_year" ON "public"."student_submissions_writing_ielts" USING "btree" ("academic_year");



CREATE INDEX "idx_ielts_student_id" ON "public"."student_submissions_writing_ielts" USING "btree" ("student_id");



CREATE INDEX "idx_ielts_task" ON "public"."student_submissions_writing_ielts" USING "btree" ("task");



CREATE INDEX "idx_ielts_user_id" ON "public"."student_submissions_writing_ielts" USING "btree" ("user_id");



CREATE INDEX "idx_linguistic_features_json" ON "public"."linguistic_features" USING "gin" ("features");



CREATE INDEX "idx_student_submissions_user_id" ON "public"."student_submissions" USING "btree" ("user_id");



CREATE INDEX "idx_text_samples_level_type" ON "public"."text_samples" USING "btree" ("cefr_level", "text_type");



CREATE OR REPLACE TRIGGER "trigger_update_overall_cefr" BEFORE INSERT OR UPDATE OF "cefr" ON "public"."student_submissions" FOR EACH ROW EXECUTE FUNCTION "public"."update_overall_cefr_trigger"();



ALTER TABLE ONLY "public"."classlists"
    ADD CONSTRAINT "classlists_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."linguistic_features"
    ADD CONSTRAINT "linguistic_features_text_id_fkey" FOREIGN KEY ("text_id") REFERENCES "public"."text_samples"("id");



ALTER TABLE ONLY "public"."linguistic_features"
    ADD CONSTRAINT "linguistic_features_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."student_submissions"
    ADD CONSTRAINT "student_submissions_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."student_submissions_writing_ielts"
    ADD CONSTRAINT "student_submissions_writing_ielts_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."text_samples"
    ADD CONSTRAINT "text_samples_cefr_level_fkey" FOREIGN KEY ("cefr_level") REFERENCES "public"."cefr_levels"("level");



ALTER TABLE ONLY "public"."text_samples"
    ADD CONSTRAINT "text_samples_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id");



CREATE POLICY "Allow users to read their own profile" ON "public"."profiles" FOR SELECT USING (("id" = ( SELECT "auth"."uid"() AS "uid")));



CREATE POLICY "Allow users to update their own profile" ON "public"."profiles" FOR UPDATE USING (("id" = ( SELECT "auth"."uid"() AS "uid"))) WITH CHECK (("id" = ( SELECT "auth"."uid"() AS "uid")));



CREATE POLICY "Allow users to update their own submissions" ON "public"."student_submissions" FOR UPDATE USING (("student_id" IN ( SELECT "profiles"."student_id"
   FROM "public"."profiles"
  WHERE ("profiles"."id" = ( SELECT "auth"."uid"() AS "uid"))))) WITH CHECK (("student_id" IN ( SELECT "profiles"."student_id"
   FROM "public"."profiles"
  WHERE ("profiles"."id" = ( SELECT "auth"."uid"() AS "uid")))));



CREATE POLICY "Enable insert for authenticated users only" ON "public"."profiles" FOR INSERT WITH CHECK (("id" = ( SELECT "auth"."uid"() AS "uid")));



CREATE POLICY "Enable read access based on Student ID" ON "public"."student_submissions" FOR SELECT USING ((("user_id" = "auth"."uid"()) OR ("student_id" IN ( SELECT "profiles"."student_id"
   FROM "public"."profiles"
  WHERE ("profiles"."id" = "auth"."uid"())))));



CREATE POLICY "Students can insert their own writing" ON "public"."student_submissions" FOR INSERT WITH CHECK (("student_id" IN ( SELECT "profiles"."student_id"
   FROM "public"."profiles"
  WHERE ("profiles"."id" = ( SELECT "auth"."uid"() AS "uid")))));



CREATE POLICY "Students can view their own submissions" ON "public"."student_submissions" FOR SELECT USING (("student_id" IN ( SELECT "profiles"."student_id"
   FROM "public"."profiles"
  WHERE ("profiles"."id" = ( SELECT "auth"."uid"() AS "uid")))));



CREATE POLICY "Superusers can view all submissions" ON "public"."student_submissions" FOR SELECT USING ((EXISTS ( SELECT 1
   FROM "public"."profiles"
  WHERE (("profiles"."id" = "auth"."uid"()) AND ("profiles"."role" = 'superuser'::"text")))));



CREATE POLICY "Users can manage their own classlists" ON "public"."classlists" TO "authenticated" USING (("auth"."uid"() = "user_id")) WITH CHECK (("auth"."uid"() = "user_id"));



ALTER TABLE "public"."classlists" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."error_reports" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."profiles" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."student_submissions" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."writing_assessment_cambridge" ENABLE ROW LEVEL SECURITY;




ALTER PUBLICATION "supabase_realtime" OWNER TO "postgres";


GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";

























































































































































GRANT ALL ON FUNCTION "public"."calculate_overall_cefr"("p_student_id" "text", "p_assessment_type" "text", "p_exam_type" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."calculate_overall_cefr"("p_student_id" "text", "p_assessment_type" "text", "p_exam_type" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."calculate_overall_cefr"("p_student_id" "text", "p_assessment_type" "text", "p_exam_type" "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."cefr_to_number"("cefr_level" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."cefr_to_number"("cefr_level" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."cefr_to_number"("cefr_level" "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."claim_student_id"("id_to_claim" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."claim_student_id"("id_to_claim" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."claim_student_id"("id_to_claim" "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."escape_sql_text"("input_text" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."escape_sql_text"("input_text" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."escape_sql_text"("input_text" "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."handle_new_user"() TO "anon";
GRANT ALL ON FUNCTION "public"."handle_new_user"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."handle_new_user"() TO "service_role";



GRANT ALL ON FUNCTION "public"."insert_speaking_assessment"("p_student_id" integer, "p_skill" "text", "p_assessment_type" "text", "p_exam_question" "text", "p_exam_type" "text", "p_student_text" "text", "p_url" "text", "p_word_count" integer, "p_overall_score" integer, "p_cefr_level" "text", "p_speaking_grammar_vocab_score" integer, "p_speaking_discourse_management_score" integer, "p_speaking_pron_score" integer, "p_speaking_interactive_communication_score" integer, "p_speaking_summary" "text", "p_speaking_grammar_vocab_comment" "text", "p_speaking_discourse_management_comment" "text", "p_speaking_pron_comment" "text", "p_speaking_interactive_communication_comment" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."insert_speaking_assessment"("p_student_id" integer, "p_skill" "text", "p_assessment_type" "text", "p_exam_question" "text", "p_exam_type" "text", "p_student_text" "text", "p_url" "text", "p_word_count" integer, "p_overall_score" integer, "p_cefr_level" "text", "p_speaking_grammar_vocab_score" integer, "p_speaking_discourse_management_score" integer, "p_speaking_pron_score" integer, "p_speaking_interactive_communication_score" integer, "p_speaking_summary" "text", "p_speaking_grammar_vocab_comment" "text", "p_speaking_discourse_management_comment" "text", "p_speaking_pron_comment" "text", "p_speaking_interactive_communication_comment" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."insert_speaking_assessment"("p_student_id" integer, "p_skill" "text", "p_assessment_type" "text", "p_exam_question" "text", "p_exam_type" "text", "p_student_text" "text", "p_url" "text", "p_word_count" integer, "p_overall_score" integer, "p_cefr_level" "text", "p_speaking_grammar_vocab_score" integer, "p_speaking_discourse_management_score" integer, "p_speaking_pron_score" integer, "p_speaking_interactive_communication_score" integer, "p_speaking_summary" "text", "p_speaking_grammar_vocab_comment" "text", "p_speaking_discourse_management_comment" "text", "p_speaking_pron_comment" "text", "p_speaking_interactive_communication_comment" "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."insert_writing_assessment"("p_student_id" integer, "p_skill" "text", "p_assessment_type" "text", "p_exam_question" "text", "p_exam_type" "text", "p_student_text" "text", "p_word_count" integer, "p_overall_score" integer, "p_cefr_level" "text", "p_content_score" integer, "p_communicative_achievement_score" integer, "p_organisation_score" integer, "p_language_score" integer, "p_summary_comment" "text", "p_content_feedback" "text", "p_communicative_achievement_feedback" "text", "p_organisation_feedback" "text", "p_language_feedback" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."insert_writing_assessment"("p_student_id" integer, "p_skill" "text", "p_assessment_type" "text", "p_exam_question" "text", "p_exam_type" "text", "p_student_text" "text", "p_word_count" integer, "p_overall_score" integer, "p_cefr_level" "text", "p_content_score" integer, "p_communicative_achievement_score" integer, "p_organisation_score" integer, "p_language_score" integer, "p_summary_comment" "text", "p_content_feedback" "text", "p_communicative_achievement_feedback" "text", "p_organisation_feedback" "text", "p_language_feedback" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."insert_writing_assessment"("p_student_id" integer, "p_skill" "text", "p_assessment_type" "text", "p_exam_question" "text", "p_exam_type" "text", "p_student_text" "text", "p_word_count" integer, "p_overall_score" integer, "p_cefr_level" "text", "p_content_score" integer, "p_communicative_achievement_score" integer, "p_organisation_score" integer, "p_language_score" integer, "p_summary_comment" "text", "p_content_feedback" "text", "p_communicative_achievement_feedback" "text", "p_organisation_feedback" "text", "p_language_feedback" "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."insert_writing_evaluation"("payload" "jsonb") TO "anon";
GRANT ALL ON FUNCTION "public"."insert_writing_evaluation"("payload" "jsonb") TO "authenticated";
GRANT ALL ON FUNCTION "public"."insert_writing_evaluation"("payload" "jsonb") TO "service_role";



GRANT ALL ON FUNCTION "public"."number_to_cefr"("num_value" numeric) TO "anon";
GRANT ALL ON FUNCTION "public"."number_to_cefr"("num_value" numeric) TO "authenticated";
GRANT ALL ON FUNCTION "public"."number_to_cefr"("num_value" numeric) TO "service_role";



GRANT ALL ON PROCEDURE "public"."safe_insert_student_submission"(IN "p_student_id" "text", IN "p_skill" "text", IN "p_assessment_type" "text", IN "p_exam_question" "text", IN "p_exam_type" "text", IN "p_student_text" "text", IN "p_word_count" integer, IN "p_overall_score" numeric, IN "p_cefr_level" "text", IN "p_content_score" numeric, IN "p_communicative_achievement_score" numeric, IN "p_organisation_score" numeric, IN "p_language_score" numeric, IN "p_summary_comment" "text", IN "p_content_feedback" "text", IN "p_communicative_achievement_feedback" "text", IN "p_organisation_feedback" "text", IN "p_language_feedback" "text") TO "anon";
GRANT ALL ON PROCEDURE "public"."safe_insert_student_submission"(IN "p_student_id" "text", IN "p_skill" "text", IN "p_assessment_type" "text", IN "p_exam_question" "text", IN "p_exam_type" "text", IN "p_student_text" "text", IN "p_word_count" integer, IN "p_overall_score" numeric, IN "p_cefr_level" "text", IN "p_content_score" numeric, IN "p_communicative_achievement_score" numeric, IN "p_organisation_score" numeric, IN "p_language_score" numeric, IN "p_summary_comment" "text", IN "p_content_feedback" "text", IN "p_communicative_achievement_feedback" "text", IN "p_organisation_feedback" "text", IN "p_language_feedback" "text") TO "authenticated";
GRANT ALL ON PROCEDURE "public"."safe_insert_student_submission"(IN "p_student_id" "text", IN "p_skill" "text", IN "p_assessment_type" "text", IN "p_exam_question" "text", IN "p_exam_type" "text", IN "p_student_text" "text", IN "p_word_count" integer, IN "p_overall_score" numeric, IN "p_cefr_level" "text", IN "p_content_score" numeric, IN "p_communicative_achievement_score" numeric, IN "p_organisation_score" numeric, IN "p_language_score" numeric, IN "p_summary_comment" "text", IN "p_content_feedback" "text", IN "p_communicative_achievement_feedback" "text", IN "p_organisation_feedback" "text", IN "p_language_feedback" "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."update_overall_cefr_trigger"() TO "anon";
GRANT ALL ON FUNCTION "public"."update_overall_cefr_trigger"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."update_overall_cefr_trigger"() TO "service_role";


















GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."cefr_levels" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."cefr_levels" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."cefr_levels" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."classlists" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."classlists" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."classlists" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."egp_statements" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."egp_statements" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."egp_statements" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."error_reports" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."error_reports" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."error_reports" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."error_reports_backup" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."error_reports_backup" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."error_reports_backup" TO "service_role";



GRANT ALL ON SEQUENCE "public"."error_reports_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."error_reports_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."error_reports_id_seq" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."linguistic_features" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."linguistic_features" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."linguistic_features" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."profiles" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."profiles" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."profiles" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."reading_lab_student_answers" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."reading_lab_student_answers" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."reading_lab_student_answers" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."reports" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."reports" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."reports" TO "service_role";



GRANT ALL ON SEQUENCE "public"."reports_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."reports_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."reports_id_seq" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."student_submissions" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."student_submissions" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."student_submissions" TO "service_role";



GRANT ALL ON SEQUENCE "public"."student_submissions_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."student_submissions_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."student_submissions_id_seq" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."student_submissions_writing_ielts" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."student_submissions_writing_ielts" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."student_submissions_writing_ielts" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."text_samples" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."text_samples" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."text_samples" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."writing_assessment_cambridge" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."writing_assessment_cambridge" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."writing_assessment_cambridge" TO "service_role";









ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLES TO "service_role";































