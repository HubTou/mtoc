#!/bin/sh
ID="@(#) $Id: mtoc_compare.sh - compare command's output (July 14, 2021) by Hubert Tournier $"

lines_count()
{
    FILENAME=$1
    cat ${FILENAME} | wc -l | sed "s/ //g"
}

is_mdoc_page()
{
    FILENAME=$1
    zcat ${FILENAME} | grep -q "^\.Sh"
}

is_man_page()
{
    FILENAME=$1
    zcat ${FILENAME} | grep -q "^\.SH"
}

extract_sh_name_section()
{
    FILENAME=$1
	zcat ${FILENAME} \
    | awk	'
        BEGIN				{in_section = 0}
        /^\.SH "?NAME"?/	{in_section = 1 ; next}
        /^\.SH/				{in_section = 0}
        in_section == 1		{print}
        '
}

strip_roff_comments()
{
    awk	'
        /^\. *$/	{next}
        /^\.\\"/	{next}
        /\\"/		{sub(/\\".*$/, "", $0)}
        /\\#/		{sub(/\\#.*$/, "", $0)}
                    {print}
        '
}

strip_roff_multi_line_macro()
{
    awk	-v MACRO=$1	'
        BEGIN			{in_macro = 0 ; pattern = "^\." MACRO}
        $0~pattern		{in_macro = 1 ; next}
        /^\.\./			{in_macro = 0 ; next}
        in_macro == 0	{print}
        '
}

strip_roff_ignore()
{
    strip_roff_multi_line_macro ig
}

strip_roff_macro_definitions()
{
    strip_roff_multi_line_macro de
}

strip_roff_format_macros()
{
    sed	-E 's/^\.(B|BI|BR|I|IB|IR|RB|RI|SM|SB) *//'
}

strip_roff_font_macros()
{
    sed	-e 's/\\f.//g'
}

strip_roff_single_line_macro()
{
    egrep -v '^\.[A-Za-z]+.*$'
}

unescape_roff_dashes()
{
    sed	-e 's/\\-/-/g' \
		-e 's/^- */ - /'
}

join_on_one_line()
{
    tr -d "\n"
}

only_keep_description()
{
    grep " - " \
    | sed -e 's/.* - //'
}

process_section()
{
    SECTION=$1

    TMP_FILE=${TMP}/$$
    ERR_COUNT=0

    DIRECTORIES=`echo ${MANPATH} | sed "s/:/ /g"`
    for DIRECTORY in $DIRECTORIES
    do
        SUBDIRECTORY=${DIRECTORY}/man${SECTION}
        if [ -d "${SUBDIRECTORY}" ]
        then
            for NAME in `ls -1 ${SUBDIRECTORY} | sort`
            do
                if [ -f "${SUBDIRECTORY}/${NAME}" ]
                then
                    FILE=`basename ${NAME} .${SECTION}.gz`
                    whatis -M ${DIRECTORY} -s ${SECTION} ${FILE} > ${TMP_FILE} 2> /dev/null
                    LINES=`lines_count ${TMP_FILE}`
                    if [ "${LINES}" = "0" ]
                    then
                        >&2 echo "DEBUG: No results for ${NAME}"
                        ERR_COUNT=`expr ${ERR_COUNT} + 1`
    
                    elif [ "${LINES}" = "1" ]
                    then
                        WHATIS=`cat ${TMP_FILE}`
                        MTOC=`mtoc -f ${SUBDIRECTORY}/${NAME}`
                        if [ "${WHATIS}" != "${MTOC}" ]
                        then
                            MTOC=`mtoc --debug -f ${SUBDIRECTORY}/${NAME} 2>&1 | egrep -v "^mtoc: DEBUG: [p{\[]"`
                            echo "${WHATIS}"
                            echo "--"
                            echo "${MTOC}"
                            echo
                        fi
    
                    else
                        if `is_mdoc_page ${SUBDIRECTORY}/${NAME}`
                        then
                            #Nm=`zcat ${SUBDIRECTORY}/${NAME} | grep "^\.Nm" | head -1 | sed "s/.Nm //"`
                            Nd=`zcat ${SUBDIRECTORY}/${NAME} | grep "^\.Nd" | sed -e "s/.Nd //" -e 's/"//g'`
                            grep "${Nd}" ${TMP_FILE} > ${TMP_FILE}.2
    
                        elif `is_man_page ${SUBDIRECTORY}/${NAME}`
                        then
                            DESC=`extract_sh_name_section ${SUBDIRECTORY}/${NAME} \
                                  | strip_roff_comments \
                                  | strip_roff_ignore \
                                  | strip_roff_macro_definitions \
                                  | strip_roff_format_macros \
                                  | strip_roff_font_macros \
                                  | strip_roff_single_line_macro \
                                  | unescape_roff_dashes \
                                  | join_on_one_line \
                                  | only_keep_description`

                            if [ "${DESC}" != "" ]
                            then
                                grep "${DESC}" ${TMP_FILE} > ${TMP_FILE}.2
                            else
                                touch ${TMP_FILE}.2
                            fi
    
                        else
                            >&2 echo "DEBUG: ${NAME} is not a man/mdoc page"
                            ERR_COUNT=`expr ${ERR_COUNT} + 1`
                            continue
                        fi
    
                        LINES=`lines_count ${TMP_FILE}.2`
                        if [ "${LINES}" = "1" ]
                        then
                            WHATIS=`cat ${TMP_FILE}.2`
                            MTOC=`mtoc -f ${SUBDIRECTORY}/${NAME}`
                            if [ "${WHATIS}" != "${MTOC}" ]
                            then
                                MTOC=`mtoc --debug -f ${SUBDIRECTORY}/${NAME} 2>&1 | egrep -v "^mtoc: DEBUG: [p{\[]"`
                                echo "${WHATIS}"
                                echo "--"
                                echo "${MTOC}"
                                echo
                            fi
                        else
                            >&2 echo "DEBUG: Several results for ${NAME}"
                            if [ "${LINES}" != "0" ]
                            then
                                cat ${TMP_FILE}.2
                            else
                                cat ${TMP_FILE}
                            fi
                            ERR_COUNT=`expr ${ERR_COUNT} + 1`

                            MTOC=`mtoc --debug -f ${SUBDIRECTORY}/${NAME} 2>&1 | egrep -v "^mtoc: DEBUG: [p{\[]"`
                            echo "--"
                            echo "${MTOC}"
                            echo
                        fi
                    fi
                    rm -f ${TMP_FILE} ${TMP_FILE}.2
                fi
            done
        fi
    done

    if [ "${ERR_COUNT}" != "0" ]
    then
        >&2 echo "DEBUG: ${ERR_COUNT} errors reported" 
    fi
}

while [ "$#" -gt "0" ]
do
    process_section $1
    shift
done

exit 0
