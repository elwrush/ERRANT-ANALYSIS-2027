


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


CREATE OR REPLACE FUNCTION "public"."current_affairs_set_response_id"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
begin
  if new.response_id is null or new.response_id = '' then
    new.response_id := coalesce(new.class_name, '') || '|' || coalesce(new.quiz_id, '') || '|' || coalesce(new.student_id, '');
  end if;
  return new;
end;
$$;


ALTER FUNCTION "public"."current_affairs_set_response_id"() OWNER TO "postgres";


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


CREATE OR REPLACE FUNCTION "public"."grammar_entry_set_response_id"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
begin
  if new.response_id is null or new.response_id = '' then
    new.response_id := coalesce(new.class_name, '') || '|' || coalesce(new.entry_id, '') || '|' || coalesce(new.student_id, '');
  end if;
  return new;
end;
$$;


ALTER FUNCTION "public"."grammar_entry_set_response_id"() OWNER TO "postgres";


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

SET default_tablespace = '';

SET default_table_access_method = "heap";


CREATE TABLE IF NOT EXISTS "public"."classlists" (
    "student_id" "text" NOT NULL,
    "name" "text" NOT NULL,
    "class" "text" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "timezone"('Asia/Bangkok'::"text", "now"()) NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "timezone"('Asia/Bangkok'::"text", "now"()) NOT NULL,
    "user_id" "uuid" DEFAULT "auth"."uid"(),
    "password_hash" "text",
    "gender" "text",
    CONSTRAINT "classlists_gender_check" CHECK ((("gender" IS NULL) OR ("gender" = ANY (ARRAY['M'::"text", 'F'::"text"])))),
    CONSTRAINT "classlists_password_hash_is_bcrypt" CHECK ((("password_hash" IS NULL) OR ("password_hash" ~ '^\$2[aby]\$'::"text")))
);


ALTER TABLE "public"."classlists" OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."set_student_password"("p_student_id" "text", "p_password" "text") RETURNS "public"."classlists"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public', 'extensions'
    AS $$
DECLARE
  v_row public.classlists;
BEGIN
  IF p_password IS NULL OR length(p_password) = 0 THEN
    RAISE EXCEPTION 'password must not be empty' USING ERRCODE = '22023';
  END IF;

  UPDATE public.classlists
     SET password_hash = extensions.crypt(p_password, extensions.gen_salt('bf', 10)),
         updated_at = now()
   WHERE student_id = p_student_id
  RETURNING * INTO v_row;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'unknown student_id %', p_student_id USING ERRCODE = 'P0002';
  END IF;

  INSERT INTO public.password_recovery (student_id, password, name, class)
  VALUES (v_row.student_id, p_password, v_row.name, v_row.class)
  ON CONFLICT (student_id) DO UPDATE
     SET password = EXCLUDED.password,
         name     = EXCLUDED.name,
         class    = EXCLUDED.class;

  RETURN v_row;
END;
$$;


ALTER FUNCTION "public"."set_student_password"("p_student_id" "text", "p_password" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."spelling_response_id"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
begin
  new.response_id := upper(new.class_name) || '|' || new.academic_year || '|' || new.term
                     || '|' || new.sitting_id || '|' || new.student_id;
  return new;
end
$$;


ALTER FUNCTION "public"."spelling_response_id"() OWNER TO "postgres";


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


CREATE OR REPLACE FUNCTION "public"."verify_student_password"("p_student_id" "text", "p_password" "text") RETURNS TABLE("student_id" "text", "name" "text", "class" "text")
    LANGUAGE "plpgsql" STABLE SECURITY DEFINER
    SET "search_path" TO 'public', 'extensions'
    AS $$
BEGIN
  RETURN QUERY
  SELECT c.student_id, c.name, c.class
  FROM classlists c
  WHERE c.student_id = p_student_id
    AND c.password_hash = crypt(p_password, c.password_hash);
END;
$$;


ALTER FUNCTION "public"."verify_student_password"("p_student_id" "text", "p_password" "text") OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."cambridge-listening-grades" (
    "id" bigint NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "student_id" "text" NOT NULL,
    "academic_year" integer NOT NULL,
    "submission_date" timestamp with time zone DEFAULT "timezone"('Asia/Bangkok'::"text", "now"()) NOT NULL,
    "assessment_type" "text" DEFAULT 'Formative'::"text",
    "exam_type" "text" DEFAULT 'PET'::"text",
    "topic" "text",
    "listening_score" numeric,
    "listening_comment" "text",
    "overall_score" numeric,
    "cefr" "text",
    "q1" integer,
    "q1_response" "text",
    "q1_category" "text",
    "q2" integer,
    "q2_response" "text",
    "q2_category" "text",
    "q3" integer,
    "q3_response" "text",
    "q3_category" "text",
    "q4" integer,
    "q4_response" "text",
    "q4_category" "text",
    "q5" integer,
    "q5_response" "text",
    "q5_category" "text",
    "q6" integer,
    "q6_response" "text",
    "q6_category" "text",
    "q7" integer,
    "q7_response" "text",
    "q7_category" "text",
    "q8" integer,
    "q8_response" "text",
    "q8_category" "text",
    "q9" integer,
    "q9_response" "text",
    "q9_category" "text",
    "q10" integer,
    "q10_response" "text",
    "q10_category" "text",
    "q11" integer,
    "q11_response" "text",
    "q11_category" "text",
    "q12" integer,
    "q12_response" "text",
    "q12_category" "text",
    "q13" integer,
    "q13_response" "text",
    "q13_category" "text",
    "q14" integer,
    "q14_response" "text",
    "q14_category" "text",
    "q15" integer,
    "q15_response" "text",
    "q15_category" "text",
    "q16" integer,
    "q16_response" "text",
    "q16_category" "text",
    "q17" integer,
    "q17_response" "text",
    "q17_category" "text",
    "q18" integer,
    "q18_response" "text",
    "q18_category" "text",
    "q19" integer,
    "q19_response" "text",
    "q19_category" "text",
    "q20" integer,
    "q20_response" "text",
    "q20_category" "text",
    "q21" integer,
    "q21_response" "text",
    "q21_category" "text",
    "q22" integer,
    "q22_response" "text",
    "q22_category" "text",
    "q23" integer,
    "q23_response" "text",
    "q23_category" "text",
    "q24" integer,
    "q24_response" "text",
    "q24_category" "text",
    "q25" integer,
    "q25_response" "text",
    "q25_category" "text",
    "percentage" integer
);


ALTER TABLE "public"."cambridge-listening-grades" OWNER TO "postgres";


COMMENT ON TABLE "public"."cambridge-listening-grades" IS 'scoring and comments for listening results at ACT Thonburi';



ALTER TABLE "public"."cambridge-listening-grades" ALTER COLUMN "id" ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME "public"."cambridge-listening-grades_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);



CREATE TABLE IF NOT EXISTS "public"."cambridge_reading_grades" (
    "id" integer NOT NULL,
    "student_id" "text" NOT NULL,
    "submission_date" timestamp with time zone DEFAULT "timezone"('Asia/Bangkok'::"text", "now"()) NOT NULL,
    "academic_year" integer NOT NULL,
    "exam_type" "text" DEFAULT 'PET'::"text",
    "assessment_type" "text" DEFAULT 'Formative'::"text",
    "topic" "text",
    "reading_score" numeric,
    "reading_average" numeric,
    "reading_comment" "text",
    "cefr" "text",
    "skill" "text",
    "max_raw" integer,
    "percentage" integer,
    "overall_score" integer,
    "class_name" "text",
    "graded_at" timestamp with time zone,
    "answer_key_id" "text",
    "q1" integer,
    "q1_response" "text",
    "q1_category" "text",
    "q2" integer,
    "q2_response" "text",
    "q2_category" "text",
    "q3" integer,
    "q3_response" "text",
    "q3_category" "text",
    "q4" integer,
    "q4_response" "text",
    "q4_category" "text",
    "q5" integer,
    "q5_response" "text",
    "q5_category" "text",
    "q6" integer,
    "q6_response" "text",
    "q6_category" "text",
    "q7" integer,
    "q7_response" "text",
    "q7_category" "text",
    "q8" integer,
    "q8_response" "text",
    "q8_category" "text",
    "q9" integer,
    "q9_response" "text",
    "q9_category" "text",
    "q10" integer,
    "q10_response" "text",
    "q10_category" "text",
    "q11" integer,
    "q11_response" "text",
    "q11_category" "text",
    "q12" integer,
    "q12_response" "text",
    "q12_category" "text",
    "q13" integer,
    "q13_response" "text",
    "q13_category" "text",
    "q14" integer,
    "q14_response" "text",
    "q14_category" "text",
    "q15" integer,
    "q15_response" "text",
    "q15_category" "text",
    "q16" integer,
    "q16_response" "text",
    "q16_category" "text",
    "q17" integer,
    "q17_response" "text",
    "q17_category" "text",
    "q18" integer,
    "q18_response" "text",
    "q18_category" "text",
    "q19" integer,
    "q19_response" "text",
    "q19_category" "text",
    "q20" integer,
    "q20_response" "text",
    "q20_category" "text",
    "q21" integer,
    "q21_response" "text",
    "q21_category" "text",
    "q22" integer,
    "q22_response" "text",
    "q22_category" "text",
    "q23" integer,
    "q23_response" "text",
    "q23_category" "text",
    "q24" integer,
    "q24_response" "text",
    "q24_category" "text",
    "q25" integer,
    "q25_response" "text",
    "q25_category" "text",
    "q26" integer,
    "q26_response" "text",
    "q26_category" "text",
    "q27" integer,
    "q27_response" "text",
    "q27_category" "text",
    "q28" integer,
    "q28_response" "text",
    "q28_category" "text",
    "q29" integer,
    "q29_response" "text",
    "q29_category" "text",
    "q30" integer,
    "q30_response" "text",
    "q30_category" "text",
    "q31" integer,
    "q31_response" "text",
    "q31_category" "text",
    "q32" integer,
    "q32_response" "text",
    "q32_category" "text"
);


ALTER TABLE "public"."cambridge_reading_grades" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."cambridge_reading_grades_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE "public"."cambridge_reading_grades_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."cambridge_reading_grades_id_seq" OWNED BY "public"."cambridge_reading_grades"."id";



CREATE TABLE IF NOT EXISTS "public"."cefr_levels" (
    "level" character varying(3) NOT NULL,
    "description" "text"
);


ALTER TABLE "public"."cefr_levels" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."current_affairs_quizzes" (
    "quiz_id" "text" NOT NULL,
    "quiz_number" integer NOT NULL,
    "quiz_date" "date" NOT NULL,
    "topic" "text" NOT NULL,
    "max_marks" numeric(4,2) DEFAULT 5 NOT NULL,
    "question_count" integer DEFAULT 5 NOT NULL,
    "key_hash" "text" NOT NULL,
    "published_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "key" "jsonb"
);


ALTER TABLE "public"."current_affairs_quizzes" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."current_affairs_scores" (
    "id" bigint NOT NULL,
    "student_id" "text" NOT NULL,
    "name" "text" NOT NULL,
    "class_name" "text" NOT NULL,
    "academic_year" integer NOT NULL,
    "term" "text" NOT NULL,
    "assessment_type" "text" DEFAULT 'CA'::"text" NOT NULL,
    "quiz_id" "text" NOT NULL,
    "quiz_score" numeric(4,2) NOT NULL,
    "status" "text" DEFAULT 'marked'::"text" NOT NULL,
    "marked_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "response_id" "text" NOT NULL,
    CONSTRAINT "cafs_quarter_marks" CHECK ((("quiz_score" >= (0)::numeric) AND ("mod"(("quiz_score" * (4)::numeric), (1)::numeric) = (0)::numeric))),
    CONSTRAINT "cafs_status_vocabulary" CHECK (("status" = ANY (ARRAY['marked'::"text", 'provisional'::"text", 'absent'::"text"])))
);


ALTER TABLE "public"."current_affairs_scores" OWNER TO "postgres";


CREATE OR REPLACE VIEW "public"."current_affairs_rankings" AS
 WITH "marked" AS (
         SELECT "s"."student_id",
            "s"."name",
            "s"."class_name",
            "s"."academic_year",
            "s"."term",
            "s"."quiz_id",
            "s"."quiz_score",
            "q"."quiz_date",
            "q"."quiz_number",
            "q"."max_marks"
           FROM ("public"."current_affairs_scores" "s"
             JOIN "public"."current_affairs_quizzes" "q" ON (("q"."quiz_id" = "s"."quiz_id")))
          WHERE ("s"."status" = 'marked'::"text")
        ), "running" AS (
         SELECT "m"."student_id",
            "m"."name",
            "m"."class_name",
            "m"."academic_year",
            "m"."term",
            "m"."quiz_id",
            "m"."quiz_score",
            "m"."quiz_date",
            "m"."quiz_number",
            "m"."max_marks",
            "sum"("m"."quiz_score") OVER "w" AS "cumulative_score",
            "sum"("m"."max_marks") OVER "w" AS "cumulative_possible",
            "count"(*) OVER "w" AS "quizzes_taken",
            "first_value"("m"."quiz_score") OVER "w" AS "base_score",
            "lag"("m"."quiz_score") OVER "w" AS "previous_score"
           FROM "marked" "m"
          WINDOW "w" AS (PARTITION BY "m"."student_id", "m"."academic_year", "m"."term" ORDER BY "m"."quiz_date", "m"."quiz_id" ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
        )
 SELECT "r"."student_id",
    "r"."name",
    "r"."class_name",
    "r"."academic_year",
    "r"."term",
    "r"."quiz_id",
    "r"."quiz_date",
    "r"."quiz_number",
    "r"."quiz_score",
    "r"."max_marks",
    "r"."quizzes_taken",
    "r"."cumulative_score",
    "r"."cumulative_possible",
    "round"((((100)::numeric * "r"."cumulative_score") / NULLIF("r"."cumulative_possible", (0)::numeric)), 1) AS "cumulative_pct",
    "round"(("r"."cumulative_score" - "r"."base_score"), 2) AS "improvement_since_base",
    "round"(("r"."cumulative_score" - ("r"."base_score" * ("r"."quizzes_taken")::numeric)), 2) AS "improvement_net",
    "round"((("r"."cumulative_score" - ("r"."base_score" * ("r"."quizzes_taken")::numeric)) / (NULLIF("r"."quizzes_taken", 0))::numeric), 2) AS "improvement_per_quiz",
        CASE
            WHEN ("r"."previous_score" IS NULL) THEN NULL::numeric
            ELSE "round"(("r"."quiz_score" - "r"."previous_score"), 2)
        END AS "latest_delta",
    "dense_rank"() OVER (PARTITION BY "r"."class_name", "r"."academic_year", "r"."term", "r"."quiz_id" ORDER BY "r"."cumulative_score" DESC) AS "rank_cumulative",
        CASE
            WHEN ("r"."quizzes_taken" < 2) THEN NULL::bigint
            ELSE "dense_rank"() OVER (PARTITION BY "r"."class_name", "r"."academic_year", "r"."term", "r"."quiz_id" ORDER BY ("r"."cumulative_score" - ("r"."base_score" * ("r"."quizzes_taken")::numeric)) DESC)
        END AS "rank_improvement",
    "dense_rank"() OVER (PARTITION BY "r"."class_name", "r"."academic_year", "r"."term", "r"."quiz_id" ORDER BY "r"."quiz_score" DESC) AS "rank_this_quiz",
    "dense_rank"() OVER (PARTITION BY "r"."academic_year", "r"."term", "r"."quiz_id" ORDER BY "r"."cumulative_score" DESC) AS "rank_school_cumulative",
        CASE
            WHEN ("r"."quizzes_taken" < 2) THEN NULL::bigint
            ELSE "dense_rank"() OVER (PARTITION BY "r"."academic_year", "r"."term", "r"."quiz_id" ORDER BY ("r"."cumulative_score" - ("r"."base_score" * ("r"."quizzes_taken")::numeric)) DESC)
        END AS "rank_school_improvement"
   FROM "running" "r";


ALTER VIEW "public"."current_affairs_rankings" OWNER TO "postgres";


COMMENT ON VIEW "public"."current_affairs_rankings" IS 'Standings as of each quiz sat: cumulative, improvement since the first quiz of the term, and the three ranks. Absentees excluded.';



ALTER TABLE "public"."current_affairs_scores" ALTER COLUMN "id" ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME "public"."current_affairs_scores_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);



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



ALTER TABLE "public"."error_reports" ALTER COLUMN "id" ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME "public"."error_reports_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);



CREATE TABLE IF NOT EXISTS "public"."grammar_entry_scores" (
    "id" bigint NOT NULL,
    "student_id" "text" NOT NULL,
    "name" "text" NOT NULL,
    "class_name" "text" NOT NULL,
    "entry_id" "text" NOT NULL,
    "score" numeric NOT NULL,
    "status" "text" DEFAULT 'marked'::"text" NOT NULL,
    "response_id" "text" NOT NULL,
    "marked_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    CONSTRAINT "grammar_entry_scores_score_check" CHECK ((("score" >= (0)::numeric) AND ("score" <= (10)::numeric))),
    CONSTRAINT "grammar_entry_scores_status_check" CHECK (("status" = ANY (ARRAY['marked'::"text", 'provisional'::"text", 'absent'::"text"])))
);


ALTER TABLE "public"."grammar_entry_scores" OWNER TO "postgres";


COMMENT ON TABLE "public"."grammar_entry_scores" IS 'One base mark per student per entry-ticket paper. No per-item columns: the paper is ten letters and the mark is the record.';



CREATE TABLE IF NOT EXISTS "public"."grammar_entry_tests" (
    "entry_id" "text" NOT NULL,
    "level" "text" NOT NULL,
    "academic_year" integer NOT NULL,
    "term" "text" NOT NULL,
    "week" integer NOT NULL,
    "week_date" "date" NOT NULL,
    "focus" "text" NOT NULL,
    "max_marks" numeric DEFAULT 10 NOT NULL,
    "key" "jsonb" NOT NULL,
    "key_hash" "text" NOT NULL,
    "published_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    CONSTRAINT "grammar_entry_tests_level_check" CHECK (("level" = ANY (ARRAY['M2'::"text", 'M3'::"text"]))),
    CONSTRAINT "grammar_entry_tests_max_marks_check" CHECK (("max_marks" > (0)::numeric)),
    CONSTRAINT "grammar_entry_tests_week_check" CHECK ((("week" >= 1) AND ("week" <= 53)))
);


ALTER TABLE "public"."grammar_entry_tests" OWNER TO "postgres";


COMMENT ON TABLE "public"."grammar_entry_tests" IS 'One row per grammar entry-ticket paper: year/week/level, the focus, and the 10-letter key.';



CREATE OR REPLACE VIEW "public"."grammar_entry_rankings" AS
 WITH "marked" AS (
         SELECT "s"."student_id",
            "s"."name",
            "s"."class_name",
            "s"."score",
            "s"."entry_id",
            "t"."level",
            "t"."academic_year",
            "t"."term",
            "t"."week",
            "t"."week_date",
            "t"."max_marks"
           FROM ("public"."grammar_entry_scores" "s"
             JOIN "public"."grammar_entry_tests" "t" ON (("t"."entry_id" = "s"."entry_id")))
          WHERE ("s"."status" = 'marked'::"text")
        ), "running" AS (
         SELECT "m"."student_id",
            "m"."name",
            "m"."class_name",
            "m"."score",
            "m"."entry_id",
            "m"."level",
            "m"."academic_year",
            "m"."term",
            "m"."week",
            "m"."week_date",
            "m"."max_marks",
            "sum"("m"."score") OVER "w" AS "cumulative_score",
            "sum"("m"."max_marks") OVER "w" AS "cumulative_possible",
            "count"(*) OVER "w" AS "entries_taken",
            "first_value"("m"."score") OVER "w" AS "base_score",
            "lag"("m"."score") OVER "w" AS "previous_score"
           FROM "marked" "m"
          WINDOW "w" AS (PARTITION BY "m"."student_id", "m"."level", "m"."academic_year", "m"."term" ORDER BY "m"."week_date", "m"."entry_id" ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
        )
 SELECT "r"."student_id",
    "r"."name",
    "r"."class_name",
    "r"."level",
    "r"."academic_year",
    "r"."term",
    "r"."entry_id",
    "r"."week",
    "r"."week_date",
    "r"."score" AS "entry_score",
    "r"."max_marks",
    "r"."entries_taken",
    "r"."cumulative_score",
    "r"."cumulative_possible",
    "round"((((100)::numeric * "r"."cumulative_score") / NULLIF("r"."cumulative_possible", (0)::numeric)), 1) AS "cumulative_pct",
    "round"(("r"."cumulative_score" - "r"."base_score"), 2) AS "improvement_since_base",
    "round"(("r"."cumulative_score" - ("r"."base_score" * ("r"."entries_taken")::numeric)), 2) AS "improvement_net",
    "round"((("r"."cumulative_score" - ("r"."base_score" * ("r"."entries_taken")::numeric)) / (NULLIF("r"."entries_taken", 0))::numeric), 2) AS "improvement_per_week",
        CASE
            WHEN ("r"."previous_score" IS NULL) THEN NULL::numeric
            ELSE "round"(("r"."score" - "r"."previous_score"), 2)
        END AS "latest_delta",
    "dense_rank"() OVER (PARTITION BY "r"."class_name", "r"."level", "r"."academic_year", "r"."term", "r"."entry_id" ORDER BY "r"."cumulative_score" DESC) AS "rank_cumulative",
        CASE
            WHEN ("r"."entries_taken" < 2) THEN NULL::bigint
            ELSE "dense_rank"() OVER (PARTITION BY "r"."class_name", "r"."level", "r"."academic_year", "r"."term", "r"."entry_id" ORDER BY ("r"."cumulative_score" - ("r"."base_score" * ("r"."entries_taken")::numeric)) DESC)
        END AS "rank_improvement",
    "dense_rank"() OVER (PARTITION BY "r"."class_name", "r"."level", "r"."academic_year", "r"."term", "r"."entry_id" ORDER BY "r"."score" DESC) AS "rank_this_week",
    "dense_rank"() OVER (PARTITION BY "r"."level", "r"."academic_year", "r"."term", "r"."entry_id" ORDER BY "r"."cumulative_score" DESC) AS "rank_school_cumulative",
        CASE
            WHEN ("r"."entries_taken" < 2) THEN NULL::bigint
            ELSE "dense_rank"() OVER (PARTITION BY "r"."level", "r"."academic_year", "r"."term", "r"."entry_id" ORDER BY ("r"."cumulative_score" - ("r"."base_score" * ("r"."entries_taken")::numeric)) DESC)
        END AS "rank_school_improvement"
   FROM "running" "r";


ALTER VIEW "public"."grammar_entry_rankings" OWNER TO "postgres";


COMMENT ON VIEW "public"."grammar_entry_rankings" IS 'Standings as of each entry ticket: cumulative mark, improvement since the first paper of the term, and the five ranks. Absentees excluded; M2 and M3 ranked separately.';



ALTER TABLE "public"."grammar_entry_scores" ALTER COLUMN "id" ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME "public"."grammar_entry_scores_id_seq"
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


CREATE TABLE IF NOT EXISTS "public"."password_recovery" (
    "student_id" "text" NOT NULL,
    "password" "text" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "timezone"('Asia/Bangkok'::"text", "now"()) NOT NULL,
    "name" "text",
    "class" "text"
);


ALTER TABLE "public"."password_recovery" OWNER TO "postgres";


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



CREATE TABLE IF NOT EXISTS "public"."speaking_assessment_cambridge" (
    "student_id" "text" NOT NULL,
    "submission_date" "date" DEFAULT CURRENT_DATE NOT NULL,
    "date" "date",
    "academic_year" integer,
    "topic" "text",
    "student_text" "text",
    "word_count" integer,
    "grammar_vocabulary_score" numeric,
    "grammar_vocabulary_feedback" "text",
    "discourse_management_score" numeric,
    "discourse_management_feedback" "text",
    "pronunciation_score" numeric,
    "pronunciation_feedback" "text",
    "interactive_communication_score" numeric,
    "interactive_communication_feedback" "text",
    "overall_score" numeric,
    "summary_comment" "text",
    "cefr" "text",
    "skill" "text" DEFAULT 'Speaking'::"text",
    "assessment_type" "text" NOT NULL,
    "exam_type" "text" NOT NULL,
    "duration_seconds" numeric,
    "audio_url" "text",
    "arguments_ideas_evidence" numeric,
    "arguments_ideas_evidence_feedback" "text",
    CONSTRAINT "speaking_assessment_cambridge_assessment_type_check" CHECK (("assessment_type" = ANY (ARRAY['CA'::"text", 'Formative'::"text", 'Term 1 Finals'::"text", 'Term 2 Finals'::"text"]))),
    CONSTRAINT "speaking_assessment_cambridge_exam_type_check" CHECK (("exam_type" = ANY (ARRAY['KEY'::"text", 'PET'::"text", 'FIRST'::"text", 'bespoke'::"text"])))
);


ALTER TABLE "public"."speaking_assessment_cambridge" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."spelling" (
    "student_id" bigint NOT NULL,
    "name" "text" NOT NULL,
    "class_name" "text" NOT NULL,
    "academic_year" integer NOT NULL,
    "term" "text" NOT NULL,
    "sitting_id" "text" NOT NULL,
    "paper" "text" DEFAULT ''::"text" NOT NULL,
    "score" integer NOT NULL,
    "max_marks" integer NOT NULL,
    "status" "text" DEFAULT 'marked'::"text" NOT NULL,
    "marked_at" timestamp with time zone,
    "response_id" "text" NOT NULL,
    "created" timestamp with time zone DEFAULT "now"() NOT NULL,
    CONSTRAINT "spelling_score_check" CHECK ((("score" >= 0) AND ("score" <= "max_marks"))),
    CONSTRAINT "spelling_status_check" CHECK (("status" = ANY (ARRAY['marked'::"text", 'absent'::"text"])))
);


ALTER TABLE "public"."spelling" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."spelling_competitions" (
    "competition_id" "text" NOT NULL,
    "academic_year" integer NOT NULL,
    "term" "text" NOT NULL,
    "sitting_id" "text" NOT NULL,
    "competition_date" "date" NOT NULL,
    "max_marks" integer NOT NULL,
    "label" "text" DEFAULT ''::"text"
);


ALTER TABLE "public"."spelling_competitions" OWNER TO "postgres";


CREATE OR REPLACE VIEW "public"."spelling_standings" AS
 WITH "joined" AS (
         SELECT "s"."student_id",
            "s"."name",
            "s"."class_name",
            "s"."academic_year",
            "s"."term",
            "s"."sitting_id",
            "s"."paper",
            "s"."score",
            "c"."max_marks",
            "c"."competition_date",
            ( SELECT "count"(*) AS "count"
                   FROM "public"."spelling_competitions" "k"
                  WHERE (("k"."academic_year" = "s"."academic_year") AND ("k"."term" = "s"."term"))) AS "sittings_in_term"
           FROM ("public"."spelling" "s"
             JOIN "public"."spelling_competitions" "c" ON ((("c"."academic_year" = "s"."academic_year") AND ("c"."term" = "s"."term") AND ("c"."sitting_id" = "s"."sitting_id"))))
          WHERE ("s"."status" = 'marked'::"text")
        ), "walked" AS (
         SELECT "j"."student_id",
            "j"."name",
            "j"."class_name",
            "j"."academic_year",
            "j"."term",
            "j"."sitting_id",
            "j"."paper",
            "j"."score",
            "j"."max_marks",
            "j"."competition_date",
            "j"."sittings_in_term",
            "count"(*) OVER "w" AS "sittings_sat",
            "sum"("j"."score") OVER "w" AS "cumulative_score",
            "sum"("j"."max_marks") OVER "w" AS "cumulative_possible",
            "first_value"("j"."score") OVER (PARTITION BY "j"."student_id", "j"."academic_year", "j"."term" ORDER BY "j"."competition_date") AS "baseline_score",
            "lag"("j"."score") OVER (PARTITION BY "j"."student_id", "j"."academic_year", "j"."term" ORDER BY "j"."competition_date") AS "previous_score"
           FROM "joined" "j"
          WINDOW "w" AS (PARTITION BY "j"."student_id", "j"."academic_year", "j"."term" ORDER BY "j"."competition_date" ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
        ), "metrics" AS (
         SELECT "walked"."student_id",
            "walked"."name",
            "walked"."class_name",
            "walked"."academic_year",
            "walked"."term",
            "walked"."sitting_id",
            "walked"."paper",
            "walked"."competition_date",
            "walked"."score",
            "walked"."max_marks",
            "walked"."sittings_sat",
            "walked"."sittings_in_term",
            "walked"."cumulative_score",
            "walked"."cumulative_possible",
            "round"(((100.0 * ("walked"."cumulative_score")::numeric) / (NULLIF("walked"."cumulative_possible", 0))::numeric), 2) AS "cumulative_pct",
            ("walked"."cumulative_score" - "walked"."baseline_score") AS "improvement_since_base",
                CASE
                    WHEN ("walked"."sittings_sat" > 1) THEN ("walked"."cumulative_score" - ("walked"."baseline_score" * "walked"."sittings_sat"))
                    ELSE NULL::bigint
                END AS "improvement_net",
                CASE
                    WHEN ("walked"."sittings_sat" > 1) THEN "round"(((1.0 * (("walked"."cumulative_score" - ("walked"."baseline_score" * "walked"."sittings_sat")))::numeric) / ("walked"."sittings_sat")::numeric), 3)
                    ELSE NULL::numeric
                END AS "improvement_per_sitting",
                CASE
                    WHEN ("walked"."previous_score" IS NULL) THEN NULL::integer
                    ELSE ("walked"."score" - "walked"."previous_score")
                END AS "latest_delta"
           FROM "walked"
        )
 SELECT "metrics"."student_id",
    "metrics"."name",
    "metrics"."class_name",
    "metrics"."academic_year",
    "metrics"."term",
    "metrics"."sitting_id",
    "metrics"."paper",
    "metrics"."competition_date",
    "metrics"."score",
    "metrics"."max_marks",
    "metrics"."sittings_sat",
    "metrics"."cumulative_score",
    "metrics"."cumulative_possible",
    "metrics"."cumulative_pct",
    "metrics"."improvement_since_base",
    "metrics"."improvement_net",
    "metrics"."improvement_per_sitting",
    "metrics"."latest_delta",
    "dense_rank"() OVER (PARTITION BY "metrics"."class_name", "metrics"."academic_year", "metrics"."term" ORDER BY "metrics"."cumulative_score" DESC) AS "rank_cumulative",
    "dense_rank"() OVER (PARTITION BY "metrics"."academic_year", "metrics"."term" ORDER BY "metrics"."cumulative_score" DESC) AS "rank_school_cumulative",
    "dense_rank"() OVER (PARTITION BY "metrics"."class_name", "metrics"."academic_year", "metrics"."term" ORDER BY "metrics"."score" DESC) AS "rank_this_sitting",
        CASE
            WHEN ("metrics"."sittings_in_term" > 1) THEN "dense_rank"() OVER (PARTITION BY "metrics"."class_name", "metrics"."academic_year", "metrics"."term" ORDER BY "metrics"."improvement_net" DESC NULLS LAST)
            ELSE NULL::bigint
        END AS "rank_improvement",
        CASE
            WHEN ("metrics"."sittings_in_term" > 1) THEN "dense_rank"() OVER (PARTITION BY "metrics"."academic_year", "metrics"."term" ORDER BY "metrics"."improvement_net" DESC NULLS LAST)
            ELSE NULL::bigint
        END AS "rank_school_improvement"
   FROM "metrics";


ALTER VIEW "public"."spelling_standings" OWNER TO "postgres";


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
    "speaking_pron_comment" "text",
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
    "academic_year" integer NOT NULL,
    CONSTRAINT "student_submissions_academic_year_check" CHECK ((("academic_year" >= 2000) AND ("academic_year" <= 2100))),
    CONSTRAINT "student_submissions_assessment_type_check" CHECK (("assessment_type" = ANY (ARRAY['Formative'::"text", 'Term 1 Midterm'::"text", 'Term 1 Finals'::"text", 'Term 2 Midterm'::"text", 'Term 2 Finals'::"text", 'CA'::"text", 'Benchmark'::"text"]))),
    CONSTRAINT "student_submissions_cefr_check" CHECK ((("cefr" IS NULL) OR ("cefr" = ANY (ARRAY['NA'::"text", 'A1'::"text", 'A1+'::"text", 'A2'::"text", 'A2+'::"text", 'B1'::"text", 'B1+'::"text", 'B2'::"text", 'B2+'::"text", 'C1'::"text", 'C1+'::"text", 'C2'::"text"])))),
    CONSTRAINT "student_submissions_exam_type_check" CHECK (("exam_type" = ANY (ARRAY['Flyers'::"text", 'Movers'::"text", 'KEY'::"text", 'PET'::"text", 'IELTS'::"text", 'FIRST'::"text"])))
);


ALTER TABLE "public"."student_submissions" OWNER TO "postgres";


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
    "topic" "text" NOT NULL,
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
    "date" "date",
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



ALTER TABLE ONLY "public"."cambridge_reading_grades" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."cambridge_reading_grades_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."reports" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."reports_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."student_submissions" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."student_submissions_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."current_affairs_scores"
    ADD CONSTRAINT "cafs_one_row_per_student_per_quiz" UNIQUE ("student_id", "quiz_id");



ALTER TABLE ONLY "public"."cambridge-listening-grades"
    ADD CONSTRAINT "cambridge-listening-grades_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."cambridge_reading_grades"
    ADD CONSTRAINT "cambridge_reading_grades_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."cefr_levels"
    ADD CONSTRAINT "cefr_levels_pkey" PRIMARY KEY ("level");



ALTER TABLE ONLY "public"."classlists"
    ADD CONSTRAINT "classlists_pkey" PRIMARY KEY ("student_id");



ALTER TABLE ONLY "public"."current_affairs_quizzes"
    ADD CONSTRAINT "current_affairs_quizzes_pkey" PRIMARY KEY ("quiz_id");



ALTER TABLE ONLY "public"."current_affairs_scores"
    ADD CONSTRAINT "current_affairs_scores_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."egp_statements"
    ADD CONSTRAINT "egp_statements_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."error_reports"
    ADD CONSTRAINT "error_reports_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."error_reports"
    ADD CONSTRAINT "error_reports_student_date_unique" UNIQUE ("student_id", "date");



ALTER TABLE ONLY "public"."grammar_entry_scores"
    ADD CONSTRAINT "grammar_entry_scores_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."grammar_entry_tests"
    ADD CONSTRAINT "grammar_entry_tests_pkey" PRIMARY KEY ("entry_id");



ALTER TABLE ONLY "public"."linguistic_features"
    ADD CONSTRAINT "linguistic_features_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."password_recovery"
    ADD CONSTRAINT "password_recovery_pkey" PRIMARY KEY ("student_id");



ALTER TABLE ONLY "public"."profiles"
    ADD CONSTRAINT "profiles_email_key" UNIQUE ("email");



ALTER TABLE ONLY "public"."profiles"
    ADD CONSTRAINT "profiles_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."profiles"
    ADD CONSTRAINT "profiles_student_id_key" UNIQUE ("student_id");



ALTER TABLE ONLY "public"."reports"
    ADD CONSTRAINT "reports_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."speaking_assessment_cambridge"
    ADD CONSTRAINT "speaking_assessment_cambridge_pkey" PRIMARY KEY ("student_id", "submission_date");



ALTER TABLE ONLY "public"."spelling_competitions"
    ADD CONSTRAINT "spelling_competitions_academic_year_term_sitting_id_key" UNIQUE ("academic_year", "term", "sitting_id");



ALTER TABLE ONLY "public"."spelling_competitions"
    ADD CONSTRAINT "spelling_competitions_pkey" PRIMARY KEY ("competition_id");



ALTER TABLE ONLY "public"."spelling"
    ADD CONSTRAINT "spelling_pkey" PRIMARY KEY ("response_id");



ALTER TABLE ONLY "public"."spelling"
    ADD CONSTRAINT "spelling_student_id_academic_year_term_sitting_id_key" UNIQUE ("student_id", "academic_year", "term", "sitting_id");



ALTER TABLE ONLY "public"."student_submissions"
    ADD CONSTRAINT "student_submissions_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."writing_assessment_cambridge"
    ADD CONSTRAINT "student_submissions_writing_cambridge_pkey" PRIMARY KEY ("student_id", "submission_date");



ALTER TABLE ONLY "public"."student_submissions_writing_ielts"
    ADD CONSTRAINT "student_submissions_writing_ielts_pkey" PRIMARY KEY ("student_id", "submission_date");



ALTER TABLE ONLY "public"."text_samples"
    ADD CONSTRAINT "text_samples_pkey" PRIMARY KEY ("id");



CREATE INDEX "cafs_quiz_class_idx" ON "public"."current_affairs_scores" USING "btree" ("quiz_id", "class_name");



CREATE INDEX "cafs_student_idx" ON "public"."current_affairs_scores" USING "btree" ("student_id");



CREATE INDEX "cafs_year_term_idx" ON "public"."current_affairs_scores" USING "btree" ("academic_year", "assessment_type");



CREATE UNIQUE INDEX "current_affairs_scores_response_id_key" ON "public"."current_affairs_scores" USING "btree" ("response_id");



CREATE UNIQUE INDEX "current_affairs_scores_student_quiz_key" ON "public"."current_affairs_scores" USING "btree" ("student_id", "quiz_id", "academic_year", "term");



CREATE UNIQUE INDEX "grammar_entry_scores_response_id_key" ON "public"."grammar_entry_scores" USING "btree" ("response_id");



CREATE UNIQUE INDEX "grammar_entry_scores_student_entry_key" ON "public"."grammar_entry_scores" USING "btree" ("student_id", "entry_id");



CREATE UNIQUE INDEX "grammar_entry_tests_week_level_key" ON "public"."grammar_entry_tests" USING "btree" ("level", "academic_year", "term", "week");



CREATE INDEX "idx_cambridge_academic_year" ON "public"."writing_assessment_cambridge" USING "btree" ("academic_year");



CREATE INDEX "idx_cambridge_cefr" ON "public"."writing_assessment_cambridge" USING "btree" ("cefr") WHERE ("cefr" IS NOT NULL);



CREATE INDEX "idx_cambridge_error_count" ON "public"."writing_assessment_cambridge" USING "btree" ("error_count") WHERE ("error_count" IS NOT NULL);



CREATE INDEX "idx_cambridge_exam_type" ON "public"."writing_assessment_cambridge" USING "btree" ("exam_type");



CREATE INDEX "idx_cambridge_student_id" ON "public"."writing_assessment_cambridge" USING "btree" ("student_id");



CREATE INDEX "idx_classlists_student_id" ON "public"."classlists" USING "btree" ("student_id");



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



CREATE OR REPLACE TRIGGER "spelling_response_id" BEFORE INSERT OR UPDATE ON "public"."spelling" FOR EACH ROW EXECUTE FUNCTION "public"."spelling_response_id"();



CREATE OR REPLACE TRIGGER "trg_current_affairs_response_id" BEFORE INSERT OR UPDATE ON "public"."current_affairs_scores" FOR EACH ROW EXECUTE FUNCTION "public"."current_affairs_set_response_id"();



CREATE OR REPLACE TRIGGER "trg_grammar_entry_response_id" BEFORE INSERT OR UPDATE ON "public"."grammar_entry_scores" FOR EACH ROW EXECUTE FUNCTION "public"."grammar_entry_set_response_id"();



CREATE OR REPLACE TRIGGER "trigger_update_overall_cefr" BEFORE INSERT OR UPDATE OF "cefr" ON "public"."student_submissions" FOR EACH ROW EXECUTE FUNCTION "public"."update_overall_cefr_trigger"();



ALTER TABLE ONLY "public"."classlists"
    ADD CONSTRAINT "classlists_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."current_affairs_scores"
    ADD CONSTRAINT "current_affairs_scores_quiz_id_fkey" FOREIGN KEY ("quiz_id") REFERENCES "public"."current_affairs_quizzes"("quiz_id") ON UPDATE CASCADE ON DELETE RESTRICT;



ALTER TABLE ONLY "public"."grammar_entry_scores"
    ADD CONSTRAINT "grammar_entry_scores_entry_id_fkey" FOREIGN KEY ("entry_id") REFERENCES "public"."grammar_entry_tests"("entry_id") ON UPDATE CASCADE ON DELETE RESTRICT;



ALTER TABLE ONLY "public"."linguistic_features"
    ADD CONSTRAINT "linguistic_features_text_id_fkey" FOREIGN KEY ("text_id") REFERENCES "public"."text_samples"("id");



ALTER TABLE ONLY "public"."linguistic_features"
    ADD CONSTRAINT "linguistic_features_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."password_recovery"
    ADD CONSTRAINT "password_recovery_student_id_fkey" FOREIGN KEY ("student_id") REFERENCES "public"."classlists"("student_id") ON DELETE CASCADE;



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



CREATE POLICY "Authenticated users can read cambridge_reading_grades" ON "public"."cambridge_reading_grades" FOR SELECT USING (("auth"."role"() = 'authenticated'::"text"));



CREATE POLICY "Enable insert for authenticated users only" ON "public"."profiles" FOR INSERT WITH CHECK (("id" = ( SELECT "auth"."uid"() AS "uid")));



CREATE POLICY "Enable read access based on Student ID" ON "public"."student_submissions" FOR SELECT USING ((("user_id" = "auth"."uid"()) OR ("student_id" IN ( SELECT "profiles"."student_id"
   FROM "public"."profiles"
  WHERE ("profiles"."id" = "auth"."uid"())))));



CREATE POLICY "Service role full access" ON "public"."classlists" TO "service_role" USING (true) WITH CHECK (true);



CREATE POLICY "Service role full access" ON "public"."password_recovery" TO "service_role" USING (true) WITH CHECK (true);



CREATE POLICY "Students can insert their own writing" ON "public"."student_submissions" FOR INSERT WITH CHECK (("student_id" IN ( SELECT "profiles"."student_id"
   FROM "public"."profiles"
  WHERE ("profiles"."id" = ( SELECT "auth"."uid"() AS "uid")))));



CREATE POLICY "Students can view their own submissions" ON "public"."student_submissions" FOR SELECT USING (("student_id" IN ( SELECT "profiles"."student_id"
   FROM "public"."profiles"
  WHERE ("profiles"."id" = ( SELECT "auth"."uid"() AS "uid")))));



CREATE POLICY "Superusers can view all submissions" ON "public"."student_submissions" FOR SELECT USING ((EXISTS ( SELECT 1
   FROM "public"."profiles"
  WHERE (("profiles"."id" = "auth"."uid"()) AND ("profiles"."role" = 'superuser'::"text")))));



CREATE POLICY "authenticated_select" ON "public"."speaking_assessment_cambridge" FOR SELECT TO "authenticated" USING (true);



ALTER TABLE "public"."cambridge-listening-grades" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."cambridge_reading_grades" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."classlists" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."current_affairs_quizzes" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."current_affairs_scores" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."error_reports" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."password_recovery" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."profiles" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "service_role_all" ON "public"."speaking_assessment_cambridge" TO "service_role" USING (true) WITH CHECK (true);



ALTER TABLE "public"."speaking_assessment_cambridge" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."spelling" ENABLE ROW LEVEL SECURITY;


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



GRANT ALL ON FUNCTION "public"."current_affairs_set_response_id"() TO "anon";
GRANT ALL ON FUNCTION "public"."current_affairs_set_response_id"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."current_affairs_set_response_id"() TO "service_role";



GRANT ALL ON FUNCTION "public"."escape_sql_text"("input_text" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."escape_sql_text"("input_text" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."escape_sql_text"("input_text" "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."grammar_entry_set_response_id"() TO "anon";
GRANT ALL ON FUNCTION "public"."grammar_entry_set_response_id"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."grammar_entry_set_response_id"() TO "service_role";



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



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."classlists" TO "service_role";



REVOKE ALL ON FUNCTION "public"."set_student_password"("p_student_id" "text", "p_password" "text") FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."set_student_password"("p_student_id" "text", "p_password" "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."spelling_response_id"() TO "anon";
GRANT ALL ON FUNCTION "public"."spelling_response_id"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."spelling_response_id"() TO "service_role";



GRANT ALL ON FUNCTION "public"."update_overall_cefr_trigger"() TO "anon";
GRANT ALL ON FUNCTION "public"."update_overall_cefr_trigger"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."update_overall_cefr_trigger"() TO "service_role";



REVOKE ALL ON FUNCTION "public"."verify_student_password"("p_student_id" "text", "p_password" "text") FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."verify_student_password"("p_student_id" "text", "p_password" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."verify_student_password"("p_student_id" "text", "p_password" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."verify_student_password"("p_student_id" "text", "p_password" "text") TO "service_role";


















GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."cambridge-listening-grades" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."cambridge-listening-grades" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."cambridge-listening-grades" TO "service_role";



GRANT ALL ON SEQUENCE "public"."cambridge-listening-grades_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."cambridge-listening-grades_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."cambridge-listening-grades_id_seq" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."cambridge_reading_grades" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."cambridge_reading_grades" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."cambridge_reading_grades" TO "service_role";



GRANT ALL ON SEQUENCE "public"."cambridge_reading_grades_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."cambridge_reading_grades_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."cambridge_reading_grades_id_seq" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."cefr_levels" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."cefr_levels" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."cefr_levels" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."current_affairs_quizzes" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."current_affairs_quizzes" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."current_affairs_quizzes" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."current_affairs_scores" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."current_affairs_scores" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."current_affairs_scores" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."current_affairs_rankings" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."current_affairs_rankings" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."current_affairs_rankings" TO "service_role";



GRANT ALL ON SEQUENCE "public"."current_affairs_scores_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."current_affairs_scores_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."current_affairs_scores_id_seq" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."egp_statements" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."egp_statements" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."egp_statements" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."error_reports" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."error_reports" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."error_reports" TO "service_role";



GRANT ALL ON SEQUENCE "public"."error_reports_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."error_reports_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."error_reports_id_seq" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."grammar_entry_scores" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."grammar_entry_scores" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."grammar_entry_scores" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."grammar_entry_tests" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."grammar_entry_tests" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."grammar_entry_tests" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."grammar_entry_rankings" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."grammar_entry_rankings" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."grammar_entry_rankings" TO "service_role";



GRANT ALL ON SEQUENCE "public"."grammar_entry_scores_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."grammar_entry_scores_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."grammar_entry_scores_id_seq" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."linguistic_features" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."linguistic_features" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."linguistic_features" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."password_recovery" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."profiles" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."profiles" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."profiles" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."reports" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."reports" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."reports" TO "service_role";



GRANT ALL ON SEQUENCE "public"."reports_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."reports_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."reports_id_seq" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."speaking_assessment_cambridge" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."speaking_assessment_cambridge" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."speaking_assessment_cambridge" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."spelling" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."spelling" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."spelling" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."spelling_competitions" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."spelling_competitions" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."spelling_competitions" TO "service_role";



GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."spelling_standings" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."spelling_standings" TO "authenticated";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."spelling_standings" TO "service_role";



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































